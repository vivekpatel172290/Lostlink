import os
from datetime import datetime, timezone
from app import create_app
from models import db, User, Item, Claim, Notification
from ml_matcher import generate_text_embedding, generate_image_embedding, find_matches

DEMO_USERS = [
    {
        "name": "Campus Administrator",
        "email": "admin@campus.edu",
        "password": "Admin@123",
        "role": "admin"
    },
    {
        "name": "Alex Rivera",
        "email": "student@campus.edu",
        "password": "Student@123",
        "role": "student"
    },
    {
        "name": "Jordan Lee",
        "email": "finder@campus.edu",
        "password": "Finder@123",
        "role": "student"
    }
]

DEMO_ITEMS = [
    {
        "item_type": "lost",
        "title": "Black OnePlus Earphones",
        "description": "Left black OnePlus wireless earphones near the library around 3 PM.",
        "location": "Library",
        "category": "Earphones",
        "contact": "+91 98765 43210 (WhatsApp)",
        "reporter_name": "Alex Rivera",
        "image_file": "earphones_item.jpg",
        "status": "open"
    },
    {
        "item_type": "found",
        "title": "Black Wireless Earphones",
        "description": "Found black wireless earphones near the library steps.",
        "location": "Library",
        "category": "Earphones",
        "contact": "security@campus.edu",
        "reporter_name": "Jordan Lee",
        "image_file": "earphones_item.jpg",
        "status": "open"
    },
    {
        "item_type": "lost",
        "title": "College ID Card",
        "description": "Lost college ID card near the canteen.",
        "location": "Canteen",
        "category": "ID Card",
        "contact": "student.help@campus.edu",
        "reporter_name": "Alex Rivera",
        "image_file": "idcard_item.jpg",
        "status": "open"
    },
    {
        "item_type": "found",
        "title": "Student ID Card",
        "description": "Found a student ID card outside the canteen.",
        "location": "Canteen",
        "category": "ID Card",
        "contact": "canteen.desk@campus.edu",
        "reporter_name": "Campus Staff",
        "image_file": "idcard_item.jpg",
        "status": "open"
    },
    {
        "item_type": "lost",
        "title": "Navy Blue College Backpack",
        "description": "Lost dark canvas university backpack containing biology textbooks near the lecture hall benches.",
        "location": "Auditorium",
        "category": "Bag / Backpack",
        "contact": "+91 99887 76655",
        "reporter_name": "Alex Rivera",
        "image_file": "backpack_item.jpg",
        "status": "open"
    },
    {
        "item_type": "found",
        "title": "Dorm Room & Bike Keys",
        "description": "Recovered a set of brass and silver keys on a gray carabiner keychain left on table 4 in the dining hall.",
        "location": "Canteen",
        "category": "Keys",
        "contact": "finder.desk@campus.edu",
        "reporter_name": "Jordan Lee",
        "image_file": "keys_item.jpg",
        "status": "open"
    }
]

def seed_database(app):
    with app.app_context():
        print("-> Re-creating database schema with updated models...")
        db.drop_all()
        db.create_all()

        print("-> Seeding default users (Admin & Students)...")
        user_map = {}
        for udata in DEMO_USERS:
            user = User(
                name=udata["name"],
                email=udata["email"],
                role=udata["role"],
                created_at=datetime.now(timezone.utc)
            )
            user.set_password(udata["password"])
            db.session.add(user)
            db.session.flush()
            user_map[udata["email"]] = user

        print("-> Seeding Section 9 benchmark items with multimodal embeddings...")
        upload_folder = app.config['UPLOAD_FOLDER']
        created_items = []

        for data in DEMO_ITEMS:
            # Check if image file exists in uploads/
            img_filename = data.get("image_file")
            img_emb = None
            if img_filename:
                img_path = os.path.join(upload_folder, img_filename)
                if os.path.exists(img_path):
                    img_emb = generate_image_embedding(img_path)

            text_emb = generate_text_embedding(data["title"], data["description"])

            # Map reporter to a user
            reporter_email = "student@campus.edu" if data["item_type"] == "lost" else "finder@campus.edu"
            user_id = user_map[reporter_email].id if reporter_email in user_map else None

            item = Item(
                user_id=user_id,
                item_type=data["item_type"],
                title=data["title"],
                description=data["description"],
                location=data["location"],
                category=data["category"],
                contact=data["contact"],
                reporter_name=data["reporter_name"],
                image_path=img_filename,
                image_embedding=img_emb,
                text_embedding=text_emb,
                status=data["status"],
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(item)
            created_items.append(item)

        db.session.commit()
        print(f"-> Successfully seeded {len(created_items)} items!")

        # Create 1 sample claim for demo testing
        found_earphones = created_items[1]
        claim = Claim(
            item_id=found_earphones.id,
            user_id=user_map["student@campus.edu"].id,
            claimant_name="Alex Rivera",
            claimant_contact="+91 98765 43210",
            proof_description="Black case with small scratch on the upper lid, paired with device named 'Alex-Buds'.",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(claim)

        # Create 1 sample notification
        notif = Notification(
            user_id=user_map["student@campus.edu"].id,
            title="High Confidence Match Found! (84.8%)",
            message="Your lost post 'Black OnePlus Earphones' matched with 'Black Wireless Earphones'.",
            link="/matches/1",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(notif)
        db.session.commit()

        # ---------------------------------------------
        # Verification per Section 9:
        # "The app should match entry 1 with entry 2 and entry 3 with entry 4."
        # ---------------------------------------------
        print("\n" + "=" * 60)
        print("VERIFYING SPECIFICATION MATCH RESULTS:")
        print("=" * 60)
        
        items = Item.query.all()
        entry1 = items[0]  # Lost Black OnePlus Earphones
        entry2 = items[1]  # Found Black Wireless Earphones
        entry3 = items[2]  # Lost College ID Card
        entry4 = items[3]  # Found Student ID Card

        candidates_found = [entry2, entry4]
        
        # Test Entry 1 matching
        matches_for_entry1 = find_matches(entry1, candidates_found, threshold=0.25, max_results=5)
        print(f"\nTarget 1: [{entry1.item_type.upper()}] '{entry1.title}'")
        for idx, m in enumerate(matches_for_entry1, 1):
            cand = m['item']
            print(f"  Match #{idx}: '{cand.title}' -> Confidence: {m['percentage']}% (Score: {m['similarity']:.4f})")

        # Test Entry 3 matching
        matches_for_entry3 = find_matches(entry3, candidates_found, threshold=0.25, max_results=5)
        print(f"\nTarget 3: [{entry3.item_type.upper()}] '{entry3.title}'")
        for idx, m in enumerate(matches_for_entry3, 1):
            cand = m['item']
            print(f"  Match #{idx}: '{cand.title}' -> Confidence: {m['percentage']}% (Score: {m['similarity']:.4f})")

        print("\n" + "=" * 60)
        print("MATCH VERIFICATION COMPLETE!")
        print("=" * 60)

if __name__ == '__main__':
    app = create_app()
    seed_database(app)
