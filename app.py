import os
import uuid
from functools import wraps
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    send_from_directory, jsonify, abort, session
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Item, Claim, Notification, Flag
from ml_matcher import (
    generate_image_embedding, 
    generate_text_embedding, 
    find_matches
)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    # -----------------------------
    # Authentication & Session Helpers
    # -----------------------------
    def get_current_user():
        user_id = session.get('user_id')
        if user_id:
            return User.query.get(user_id)
        return None

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not get_current_user():
                flash('Please log in with your college account to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user or not user.is_admin():
                flash('Admin credentials required for this action.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    @app.context_processor
    def inject_context():
        user = get_current_user()
        unread_count = 0
        if user:
            unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        return {
            'current_user': user,
            'unread_notifications_count': unread_count,
            'app_name': 'LostLink'
        }

    # -----------------------------
    # Core Public Feed & Search
    # -----------------------------
    @app.route('/')
    def index():
        """
        Home & Explore page:
        Features Coder Army hero with dynamic animated headline,
        illuminated auto-scrolling ticker box of Lost & Found cards,
        live statistics, and a 3-column feed with category & location filters.
        """
        item_type = request.args.get('item_type', '').strip().lower()
        category = request.args.get('category', '').strip()
        location = request.args.get('location', '').strip()
        date_sort = request.args.get('date_sort', 'newest').strip().lower()
        search_query = request.args.get('q', '').strip()
        status_filter = request.args.get('status', 'open').strip().lower()

        # Build query
        query = Item.query

        if status_filter == 'open':
            query = query.filter_by(status='open')
        elif status_filter in ['matched', 'resolved']:
            query = query.filter_by(status=status_filter)

        if item_type in ['lost', 'found']:
            query = query.filter_by(item_type=item_type)

        if category:
            query = query.filter(Item.category.ilike(f"%{category}%"))

        if location:
            query = query.filter(Item.location.ilike(f"%{location}%"))

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (Item.title.ilike(search_pattern)) | 
                (Item.description.ilike(search_pattern)) |
                (Item.location.ilike(search_pattern)) |
                (Item.category.ilike(search_pattern))
            )

        if date_sort == 'oldest':
            query = query.order_by(Item.created_at.asc())
        else:
            query = query.order_by(Item.created_at.desc())

        items = query.all()

        # Metrics for hero stat cards
        total_open_lost = Item.query.filter_by(item_type='lost', status='open').count()
        total_open_found = Item.query.filter_by(item_type='found', status='open').count()
        total_resolved = Item.query.filter(Item.status.in_(['matched', 'resolved'])).count()
        total_items = Item.query.count()

        # Unique categories and locations for filter dropdowns
        all_categories = sorted(list(set(i.category for i in Item.query.all() if i.category)))
        all_locations = sorted(list(set(i.location for i in Item.query.all() if i.location)))

        # Showcase items for the vertical auto-scrolling ticker box
        showcase_items = Item.query.order_by(Item.created_at.desc()).limit(8).all()

        return render_template(
            'index.html',
            items=items,
            showcase_items=showcase_items,
            item_type=item_type,
            category=category,
            location=location,
            date_sort=date_sort,
            search_query=search_query,
            status_filter=status_filter,
            total_open_lost=total_open_lost,
            total_open_found=total_open_found,
            total_resolved=total_resolved,
            total_items=total_items,
            all_categories=all_categories,
            all_locations=all_locations
        )

    # -----------------------------
    # Report Item (Lost or Found)
    # -----------------------------
    @app.route('/report', methods=['GET', 'POST'])
    @app.route('/post', methods=['GET', 'POST'])
    def post_item():
        """
        Report a Lost or Found item.
        Accepts title, description, category, location, contact, and optional photo.
        Generates CLIP image & text embeddings, stores in SQLite, and redirects to AI Matches page.
        """
        user = get_current_user()

        if request.method == 'POST':
            item_type = request.form.get('item_type', '').strip().lower()
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            location = request.form.get('location', '').strip()
            contact = request.form.get('contact', '').strip()
            uploaded_file = request.files.get('image')

            # Validation per PDF requirement #20
            if not title or not description or not category or not location or not contact:
                flash('Please complete all required fields (title, description, category, location, contact).', 'danger')
                return render_template('post_item.html')

            if item_type not in ['lost', 'found']:
                flash('Please choose whether this item is Lost or Found.', 'danger')
                return render_template('post_item.html')

            # Handle Image Upload & Validation
            image_filename = None
            image_abs_path = None
            if uploaded_file and uploaded_file.filename != '':
                if allowed_file(uploaded_file.filename):
                    original_name = secure_filename(uploaded_file.filename)
                    unique_filename = f"{uuid.uuid4().hex[:12]}_{original_name}"
                    image_abs_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    uploaded_file.save(image_abs_path)
                    image_filename = unique_filename
                else:
                    flash('Invalid image format. Supported formats: PNG, JPG, JPEG, WEBP.', 'warning')

            # Generate CLIP Embeddings
            img_emb = None
            if image_abs_path and os.path.exists(image_abs_path):
                img_emb = generate_image_embedding(image_abs_path)

            txt_emb = generate_text_embedding(title, description)

            reporter_name = user.name if user else "Campus Student"
            user_id = user.id if user else None

            new_item = Item(
                user_id=user_id,
                item_type=item_type,
                title=title,
                description=description,
                category=category,
                location=location,
                contact=contact,
                reporter_name=reporter_name,
                image_path=image_filename,
                image_embedding=img_emb,
                text_embedding=txt_emb,
                status="open",
                created_at=datetime.now(timezone.utc)
            )

            db.session.add(new_item)
            db.session.commit()

            # Automatic check for opposite matches to trigger in-app notification
            opposite_type = 'found' if item_type == 'lost' else 'lost'
            candidates = Item.query.filter_by(item_type=opposite_type, status='open').all()
            matches = find_matches(new_item, candidates, threshold=app.config['SIMILARITY_THRESHOLD'], max_results=3)

            if matches and user:
                top = matches[0]
                if top['percentage'] >= 70:
                    notif = Notification(
                        user_id=user.id,
                        title=f"High Confidence Match Found! ({top['percentage']}%)",
                        message=f"Your {item_type} post '{title}' matched with '{top['item'].title}'.",
                        link=url_for('matches', item_id=new_item.id)
                    )
                    db.session.add(notif)
                    db.session.commit()

            flash(f"Your {item_type.capitalize()} item was published to LostLink! Reviewing AI matches...", "success")
            return redirect(url_for('matches', item_id=new_item.id))

        return render_template('post_item.html')

    # -----------------------------
    # AI Matches Results Page
    # -----------------------------
    @app.route('/matches/<int:item_id>')
    def matches(item_id):
        """
        AI Match Results page per Section 6 & PDF Layout specs:
        - Prominently showcases the best match side-by-side with comparison cards
        - Interactive similarity confidence bar & match percentage
        - Actions: View Item, Contact Reporter, Confirm Match, Reject Match
        - Displays remaining top candidates in smaller cards
        """
        target_item = Item.query.get_or_404(item_id)
        opposite_type = 'found' if target_item.item_type == 'lost' else 'lost'
        candidates = Item.query.filter_by(item_type=opposite_type).filter(Item.status.in_(['open', 'matched'])).all()

        top_matches = find_matches(
            target_item=target_item,
            candidate_items=candidates,
            threshold=app.config['SIMILARITY_THRESHOLD'],
            max_results=app.config['MAX_MATCH_RESULTS']
        )

        best_match = top_matches[0] if top_matches else None
        other_matches = top_matches[1:] if len(top_matches) > 1 else []

        return render_template(
            'matches.html',
            target_item=target_item,
            matches=top_matches,
            best_match=best_match,
            other_matches=other_matches,
            opposite_type=opposite_type
        )

    @app.route('/matches/<int:item_id>/confirm/<int:match_id>', methods=['POST'])
    def confirm_match(item_id, match_id):
        """
        Match Confirmation per PDF specification #25:
        User confirms a suggested match, transitioning both items to 'matched'.
        """
        item1 = Item.query.get_or_404(item_id)
        item2 = Item.query.get_or_404(match_id)

        item1.status = 'matched'
        item1.matched_with_id = item2.id
        item2.status = 'matched'
        item2.matched_with_id = item1.id

        # Send notifications if users exist
        if item1.user_id:
            db.session.add(Notification(
                user_id=item1.user_id,
                title="Match Confirmed!",
                message=f"Your post '{item1.title}' has been matched with '{item2.title}'.",
                link=url_for('item_details', item_id=item1.id)
            ))
        if item2.user_id:
            db.session.add(Notification(
                user_id=item2.user_id,
                title="Match Confirmed!",
                message=f"Your post '{item2.title}' has been matched with '{item1.title}'.",
                link=url_for('item_details', item_id=item2.id)
            ))

        db.session.commit()
        flash(f"Match confirmed! Both items #{item1.id} and #{item2.id} have been updated to 'Matched'.", "success")
        return redirect(url_for('matches', item_id=item1.id))

    # -----------------------------
    # Item Details & Actions
    # -----------------------------
    @app.route('/item/<int:item_id>')
    def item_details(item_id):
        """
        Full item details view:
        - Image, badges, title, category, location, date, full description
        - Protected Contact Reporter feature (reveals on click or modal)
        - Claim Found Item workflow for found items
        - Reporter quick controls (Edit, Delete, Resolve)
        - Related opposite AI matches below
        """
        item = Item.query.get_or_404(item_id)

        opposite_type = 'found' if item.item_type == 'lost' else 'lost'
        candidates = Item.query.filter_by(item_type=opposite_type, status='open').all()
        related_matches = find_matches(
            target_item=item,
            candidate_items=candidates,
            threshold=app.config['SIMILARITY_THRESHOLD'],
            max_results=3
        )

        return render_template(
            'item_detail.html',
            item=item,
            related_matches=related_matches
        )

    @app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
    def edit_item(item_id):
        """
        Edit own post per PDF specification #17.
        """
        item = Item.query.get_or_404(item_id)
        current_user = get_current_user()

        # Authorization check: only reporter or admin
        if current_user and item.user_id and item.user_id != current_user.id and not current_user.is_admin():
            flash('You do not have permission to edit this report.', 'danger')
            return redirect(url_for('item_details', item_id=item.id))

        if request.method == 'POST':
            item.title = request.form.get('title', item.title).strip()
            item.description = request.form.get('description', item.description).strip()
            item.category = request.form.get('category', item.category).strip()
            item.location = request.form.get('location', item.location).strip()
            item.contact = request.form.get('contact', item.contact).strip()

            uploaded_file = request.files.get('image')
            if uploaded_file and uploaded_file.filename != '':
                if allowed_file(uploaded_file.filename):
                    original_name = secure_filename(uploaded_file.filename)
                    unique_filename = f"{uuid.uuid4().hex[:12]}_{original_name}"
                    image_abs_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    uploaded_file.save(image_abs_path)
                    item.image_path = unique_filename
                    item.image_embedding = generate_image_embedding(image_abs_path)

            # Re-generate text embedding
            item.text_embedding = generate_text_embedding(item.title, item.description)

            db.session.commit()
            flash(f"Report #{item.id} has been updated successfully.", "success")
            return redirect(url_for('item_details', item_id=item.id))

        return render_template('edit_item.html', item=item)

    @app.route('/item/<int:item_id>/delete', methods=['POST'])
    def delete_item(item_id):
        """
        Delete own post per PDF specification #18.
        """
        item = Item.query.get_or_404(item_id)
        current_user = get_current_user()

        # Authorization: reporter or admin
        if current_user and item.user_id and item.user_id != current_user.id and not current_user.is_admin():
            flash('You do not have permission to delete this report.', 'danger')
            return redirect(url_for('item_details', item_id=item.id))

        # Remove image file if stored
        if item.image_path:
            p = os.path.join(app.config['UPLOAD_FOLDER'], item.image_path)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

        db.session.delete(item)
        db.session.commit()
        flash(f"Report #{item_id} has been removed.", "info")
        return redirect(url_for('my_reports') if current_user else url_for('index'))

    @app.route('/item/<int:item_id>/resolve', methods=['POST'])
    def resolve_item(item_id):
        """
        Mark item as Resolved / Returned per PDF specification #16.
        """
        item = Item.query.get_or_404(item_id)
        item.status = 'resolved' if item.status != 'resolved' else 'open'
        db.session.commit()
        state = 'Resolved / Returned' if item.status == 'resolved' else 'Reopened'
        flash(f"Item #{item.id} is now marked as {state}.", "success")
        return redirect(url_for('item_details', item_id=item.id))

    @app.route('/item/<int:item_id>/claim', methods=['GET', 'POST'])
    def claim_item(item_id):
        """
        Claim a Found item per PDF specification #23 & #24:
        Claimant answers ownership questions (color, brand, contents, identifying marks)
        which are verified before contact details or physical handover.
        """
        item = Item.query.get_or_404(item_id)
        user = get_current_user()

        if request.method == 'POST':
            claimant_name = request.form.get('name', user.name if user else '').strip()
            claimant_contact = request.form.get('contact', '').strip()
            proof = request.form.get('proof', '').strip()

            if not claimant_name or not claimant_contact or not proof:
                flash('Please complete all verification fields to submit your claim.', 'danger')
                return render_template('claim_item.html', item=item)

            claim = Claim(
                item_id=item.id,
                user_id=user.id if user else None,
                claimant_name=claimant_name,
                claimant_contact=claimant_contact,
                proof_description=proof,
                status='pending',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(claim)

            # Notify item reporter
            if item.user_id:
                db.session.add(Notification(
                    user_id=item.user_id,
                    title="New Ownership Claim Received",
                    message=f"{claimant_name} submitted an ownership claim for your found item '{item.title}'.",
                    link=url_for('item_details', item_id=item.id)
                ))

            db.session.commit()
            flash('Your ownership claim has been submitted to the finder and campus security for verification.', 'success')
            return redirect(url_for('item_details', item_id=item.id))

        return render_template('claim_item.html', item=item)

    @app.route('/item/<int:item_id>/flag', methods=['POST'])
    def flag_item(item_id):
        """
        Report abuse or spam post per PDF specification #29.
        """
        item = Item.query.get_or_404(item_id)
        reason = request.form.get('reason', 'Suspicious or duplicate listing').strip()
        user = get_current_user()
        reporter = user.name if user else "Anonymous Student"

        flag = Flag(
            item_id=item.id,
            reason=reason,
            reported_by=reporter,
            created_at=datetime.now(timezone.utc)
        )
        item.flag_count += 1
        db.session.add(flag)
        db.session.commit()

        flash(f"Post #{item.id} has been flagged for campus admin review.", "info")
        return redirect(url_for('item_details', item_id=item.id))

    # -----------------------------
    # User Dashboard & Profile
    # -----------------------------
    @app.route('/my-reports')
    @login_required
    def my_reports():
        """
        User's personal dashboard per PDF specification #22:
        Lists all reports created by the logged-in student with quick actions.
        """
        user = get_current_user()
        status_filter = request.args.get('status', 'all').strip().lower()

        query = Item.query.filter_by(user_id=user.id)
        if status_filter in ['lost', 'found']:
            query = query.filter_by(item_type=status_filter)
        elif status_filter in ['open', 'matched', 'resolved']:
            query = query.filter_by(status=status_filter)

        my_items = query.order_by(Item.created_at.desc()).all()

        return render_template(
            'my_reports.html',
            items=my_items,
            status_filter=status_filter,
            user=user
        )

    @app.route('/profile')
    @login_required
    def profile():
        """
        User Profile page per PDF specification #21:
        Displays student information, active count, resolved count, and recent activity.
        """
        user = get_current_user()
        recent_items = Item.query.filter_by(user_id=user.id).order_by(Item.created_at.desc()).limit(5).all()
        return render_template('profile.html', user=user, recent_items=recent_items)

    @app.route('/notifications')
    @login_required
    def notifications():
        """
        In-app notifications feed per PDF specification #26.
        """
        user = get_current_user()
        all_notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
        # Mark all as read
        for n in all_notifs:
            n.is_read = True
        db.session.commit()
        return render_template('notifications.html', notifications=all_notifs)

    # -----------------------------
    # Authentication (Login / Signup)
    # -----------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Student & Admin Login per PDF specification #1.
        """
        if get_current_user():
            return redirect(url_for('index'))

        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                flash(f"Welcome back to LostLink, {user.name}!", "success")
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('index'))
            else:
                flash('Invalid email or password. Please try again.', 'danger')

        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        """
        Student Registration per PDF specification #1.
        """
        if get_current_user():
            return redirect(url_for('index'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not name or not email or not password:
                flash('Please fill in all registration fields.', 'danger')
                return render_template('signup.html')

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('signup.html')

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('signup.html')

            if User.query.filter_by(email=email).first():
                flash('An account with this email already exists. Please log in.', 'warning')
                return redirect(url_for('login'))

            new_user = User(
                name=name,
                email=email,
                role='student',
                created_at=datetime.now(timezone.utc)
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id
            flash('Your LostLink account was created successfully! You are now logged in.', 'success')
            return redirect(url_for('index'))

        return render_template('signup.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out safely.', 'info')
        return redirect(url_for('index'))

    # -----------------------------
    # Admin Moderation Dashboard
    # -----------------------------
    @app.route('/admin')
    def admin_dashboard():
        """
        Admin Moderation Dashboard per PDF specifications #28, #30, #31, #32:
        - View summary metrics (Total, Open, Matched, Resolved, Claims, Flags)
        - Moderate items (Resolve, Reopen, Delete spam)
        - Review claims queue (Approve, Reject)
        - Review flagged spam queue
        """
        items = Item.query.order_by(Item.created_at.desc()).all()
        claims = Claim.query.order_by(Claim.created_at.desc()).all()
        flags = Flag.query.order_by(Flag.created_at.desc()).all()

        total_items = len(items)
        open_items = sum(1 for i in items if i.status == 'open')
        matched_items = sum(1 for i in items if i.status == 'matched')
        resolved_items = sum(1 for i in items if i.status == 'resolved')
        pending_claims = sum(1 for c in claims if c.status == 'pending')
        flagged_count = len(flags)

        return render_template(
            'admin.html',
            items=items,
            claims=claims,
            flags=flags,
            total_items=total_items,
            open_items=open_items,
            matched_items=matched_items,
            resolved_items=resolved_items,
            pending_claims=pending_claims,
            flagged_count=flagged_count
        )

    @app.route('/admin/claim/<int:claim_id>/<action>', methods=['POST'])
    def admin_claim_action(claim_id, action):
        claim = Claim.query.get_or_404(claim_id)
        if action in ['approve', 'reject']:
            claim.status = 'approved' if action == 'approve' else 'rejected'
            if action == 'approve':
                claim.item.status = 'resolved'
            db.session.commit()
            flash(f"Claim #{claim.id} has been marked as '{claim.status}'.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/flag/<int:flag_id>/dismiss', methods=['POST'])
    def admin_flag_dismiss(flag_id):
        flag = Flag.query.get_or_404(flag_id)
        db.session.delete(flag)
        db.session.commit()
        flash(f"Flag report #{flag_id} dismissed.", "info")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/delete/<int:item_id>', methods=['POST'])
    def admin_delete(item_id):
        item = Item.query.get_or_404(item_id)
        if item.image_path:
            img_file = os.path.join(app.config['UPLOAD_FOLDER'], item.image_path)
            if os.path.exists(img_file):
                try:
                    os.remove(img_file)
                except OSError:
                    pass
        db.session.delete(item)
        db.session.commit()
        flash(f"Post #{item_id} has been permanently deleted.", "info")
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/toggle-status/<int:item_id>', methods=['POST'])
    def admin_toggle_status(item_id):
        item = Item.query.get_or_404(item_id)
        item.status = 'open' if item.status == 'resolved' else 'resolved'
        db.session.commit()
        flash(f"Status for #{item_id} changed to '{item.status}'.", "success")
        return redirect(url_for('admin_dashboard'))

    # -----------------------------
    # Media & Static Routes
    # -----------------------------
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'images'),
            'default-item.svg',
            mimetype='image/svg+xml'
        )

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # -----------------------------
    # REST API Endpoints (Section 10 & 50)
    # -----------------------------
    @app.route('/api/matches/<int:item_id>')
    def api_matches(item_id):
        target = Item.query.get_or_404(item_id)
        opposite_type = 'found' if target.item_type == 'lost' else 'lost'
        candidates = Item.query.filter_by(item_type=opposite_type, status='open').all()
        matches_data = find_matches(
            target, candidates, 
            threshold=app.config['SIMILARITY_THRESHOLD'], 
            max_results=app.config['MAX_MATCH_RESULTS']
        )
        return jsonify({
            'target_item': target.to_dict(),
            'matches': [
                {
                    'item': m['item'].to_dict(),
                    'similarity': m['similarity'],
                    'percentage': m['percentage'],
                    'match_type': m['match_type']
                } for m in matches_data
            ]
        })

    @app.route('/api/items')
    def api_items():
        items = Item.query.order_by(Item.created_at.desc()).limit(20).all()
        return jsonify([i.to_dict() for i in items])

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
