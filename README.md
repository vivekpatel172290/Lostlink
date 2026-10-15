# ⚡ LostLink — AI-Powered Campus Lost & Found System

> **Next-Generation Campus Lost & Found Platform with Vision-Language Multimodal AI Matching & Coder Army Cyber Aesthetics**  
> *Engineered per the Complete Recover & Campus Lost & Found Specification (PDFs 1 & 2)*

---

## 📌 1. Project Overview & Problem Statement
Campus students frequently misplace essential daily belongings such as **student ID cards, wireless earbuds, smartphones, laptops, backpacks, dorm keys, water bottles, and textbooks**. 

Traditionally, lost & found information is fragmented across chaotic WhatsApp chats, Discord servers, and notice boards. This lack of structure causes low recovery rates and lengthy delays.

**LostLink** delivers an end-to-end, privacy-conscious platform powered by **OpenAI CLIP ViT-B-32 Multimodal AI**. It instantly correlates lost reports against found reports using joint vision and semantic text embeddings, achieving real-time match rankings with high precision.

---

## 🎨 2. Visual Identity & Coder Army Aesthetics
Built with a dark cyber design inspired by **Coder Army**:
- **Palette:** Obsidian background (`#070913`, `#0E1322`), neon cyan (`#00F2FE`), electric indigo (`#6366F1`), glowing crimson red for **Lost** (`#EF4444`), glowing emerald green for **Found** (`#10B981`), and cyber purple for **AI Match Confidence** (`#A855F7`).
- **Typography:** Modern Google Font pairings (`Outfit` & `Inter`).
- **Dynamic Headline Rotator:** Animated typewriter/ticker switching seamlessly across key campus recovery themes.
- **Hero Auto-Scrolling Showcase Box:** Replaced static or code boxes with an illuminated cyber showcase where high-resolution photos and details of real lost & found items continuously scroll upwards (`scroll in up in box`).
- **Glassmorphism & Glowing Borders:** Subtle glowing shadows (`box-shadow: 0 0 25px rgba(...)`), pill tags, neon hover elevations, and responsive transitions.

---

## 🚀 3. Features Implemented (PDF Checklist 1–35)

### Must-Have Functions (MVP — Functions 1–20)
1. **User Registration & Login:** Secure student onboarding with hashed passwords (`werkzeug.security`), session persistence, and college email format checks.
2. **Post Lost Item:** Submit title, description, category, campus location, date/time, contact number/email, and photo.
3. **Post Found Item:** Dedicated found flow with the same rich metadata schema.
4. **Image Upload & Live Preview:** Instant client-side drag-and-drop preview, file format validation (PNG, JPG, JPEG, WEBP), and 16MB file limit.
5. **Item Listing Feed:** Clean 3-column card grid displaying photos, Lost/Found badges, category, location, and relative timestamps (`time_ago`).
6. **Item Details View:** Complete breakdown of item attributes, uploaded photo zoom, reporter name, and secure interactive action triggers.
7. **Search Engine:** Real-time query matching across item titles, descriptions, categories, and campus locations.
8. **Multi-Faceted Filters:** Filter by Lost/Found status, category dropdown, campus location, and date sorting.
9. **CLIP Image Embeddings:** 512-dimensional normalized vision vectors generated via `clip-ViT-B-32`.
10. **CLIP Text Embeddings:** Joint vision-language semantic vectors from titles and item descriptions.
11. **Automatic AI Matching:** Bidirectional comparison (Lost $\leftrightarrow$ Found) executed upon post submission.
12. **Similarity Scoring:** Cosine similarity formatted as intuitive percentage scores (e.g., `87% Match`).
13. **Match Results Page:** Top candidate comparison with side-by-side card comparison, glowing similarity progress bars, and match confirmation actions.
14. **Match Threshold:** Automated filtering ensuring candidates meet a 25% minimum confidence threshold (`threshold >= 0.25`).
15. **Protected Contact Reporter:** Hidden-by-default phone number and email with an interactive reveal button, one-click WhatsApp launcher, direct phone calling, and email links.
16. **Mark as Resolved:** Reporters can mark recovered items as returned/resolved.
17. **Edit Own Post:** Editable fields for title, description, location, category, and photo.
18. **Delete Own Post:** Secure removal restricted to post owners or administrators.
19. **Report Status Lifecycle:** Discrete status states: `Open`, `Matched`, and `Resolved`.
20. **Form Validation:** Input validation, email syntax enforcement, and clear inline user flash feedback.

### Important & Trust Functions (Functions 21–35)
21. **User Profile:** Shows user name, college email, role, active reports counter, and resolved reports counter.
22. **My Reports Dashboard:** Horizontal list layout for rapid scanning, status badges, direct links to AI matches, quick editing, and one-click resolution.
23. **Claim Found Item:** Multi-question ownership claim workflow (brand, color, identifying marks, serial numbers).
24. **Claim Verification:** Claim records reviewable in the Admin Moderation Queue before contact disclosure.
25. **Match Confirmation:** One-click confirmation workflow linking mutual reports into `Matched` status.
26. **In-App Notifications:** Real-time alert notifications for new AI match candidates and submitted claims.
27. **Notification Center:** Dedicated `/notifications` hub with read/unread tracking.
28. **Admin Dashboard:** Central console at `/admin` displaying real-time metrics (Total Items, AI Matches, Claims, Recovery Rate %).
29. **Report Abuse / Spam:** Flagging mechanism enabling users to report suspicious, duplicate, or offensive posts.
30. **Admin Moderation Queue:** Dedicated admin tab to review flagged posts and resolve or delete them.
31. **Category Management:** Structured support for ID Cards, Phones, Earphones, Bags, Keys, Laptops, Books, and Wallets.
32. **Location Management:** Campus zones (Library, Canteen, Hostel Block A/B, Main Gate, Sports Complex, Computer Lab, Lecture Hall).
33. **Activity Logs & Audit Trail:** Automatic timestamping for creation, editing, matching, claiming, and resolution.
34. **REST API Endpoints:** JSON endpoints (`/api/items`, `/api/matches/<id>`) ready for mobile/external integrations.
35. **Fully Responsive Design:** Optimized 12-column layout conforming to desktop (1024px+), tablet (640-1023px), and mobile (<640px).

---

## 🛠️ 4. Technology Stack
| Layer | Technologies Used |
|---|---|
| **Frontend** | HTML5, CSS3 (Vanilla Coder Army Cyber Theme), JavaScript (ES6+), Jinja2 |
| **Backend** | Python Flask 3.x, Werkzeug Security (Bcrypt password hashing) |
| **Database** | SQLite3 with Flask-SQLAlchemy ORM (Pickle BLOB for 512D embeddings) |
| **Multimodal AI** | `sentence-transformers/clip-ViT-B-32`, NumPy Cosine Dot Product |
| **Image Processing** | Pillow (PIL) for aspect ratio correction, resizing, and format validation |
| **Asset Delivery** | Real high-resolution campus demo assets + SVG vector fallbacks |

---

## 📂 5. Project Architecture & File Tree
```
project_2/
├── app.py                     # Flask web app, routes, auth logic, and API endpoints
├── config.py                  # Database paths, file limits, and ML thresholds
├── models.py                  # SQLAlchemy models (User, Item, Claim, Notification, Flag)
├── ml_matcher.py              # CLIP embedding pipeline & cosine similarity engine
├── seed.py                    # Section 9 benchmark demo seed script
├── test_routes.py             # Automated end-to-end endpoint & AI test suite
├── requirements.txt           # Python dependency manifest
├── README.md                  # Project documentation & reference
├── uploads/                   # Stored user-uploaded item photos
├── static/
│   ├── css/
│   │   └── style.css          # Coder Army cyber theme, glowing accents, ticker box keyframes
│   ├── js/
│   │   └── main.js            # Headline rotator, photo preview, dropzone, contact reveal
│   └── images/
│       ├── earphones_item.jpg # Realistic OnePlus earbuds image
│       ├── idcard_item.jpg    # Realistic student ID card image
│       ├── backpack_item.jpg  # Realistic navy campus backpack image
│       ├── keys_item.jpg      # Realistic brass carabiner keys image
│       └── default-item.svg   # Fallback cyber neural network link graphic
└── templates/
    ├── base.html              # Top navigation, brand logo, user session menu, footer
    ├── index.html             # Hero with dynamic rotator & scrolling box, filters, feed
    ├── post_item.html         # Report Lost/Found form with drag-and-drop preview
    ├── matches.html           # Side-by-side AI match comparison & confirmation
    ├── item_detail.html       # Full item view, protected contact, claim & flag modals
    ├── my_reports.html        # Horizontal management rows for user reports
    ├── edit_item.html         # Edit existing report details
    ├── claim_item.html        # Multi-question ownership verification form
    ├── profile.html           # User profile & stats
    ├── notifications.html     # In-app notification center
    ├── login.html             # User login card
    ├── signup.html            # User registration card
    └── admin.html             # Metrics, item catalog, claims queue, flagged spam queue
```

---

## ⚡ 6. Quick Start & Execution

### 1. Activate Environment & Install Dependencies
```bash
# Windows PowerShell
.\venv\Scripts\activate

# Install dependencies if needed
pip install -r requirements.txt
```

### 2. Seed Demo Benchmark Data
Populate the database with benchmark pairs, sample users, claims, and verified embeddings:
```bash
python seed.py
```

### 3. Run the Automated Test Suite
Verify that all routes, auth sessions, and AI matching pass:
```bash
python test_routes.py
```

### 4. Launch the Dev Server
```bash
python app.py
```
Navigate to: **`http://127.0.0.1:5000`** in your browser.

---

## 🔑 7. Demo Credentials
| Role | Email | Password | Permissions |
|---|---|---|---|
| **Campus Admin** | `admin@campus.edu` | `Admin@123` | Full moderation, claims review, flagged queue, item deletion |
| **Student** | `student@campus.edu` | `Student@123` | Report items, view matches, claim items, manage own reports |

---

## 🏆 8. Benchmark AI Matching Scenarios
The system is pre-seeded with the 4 benchmark test cases:
1. **Lost:** *Black OnePlus Earphones* (Library) $\leftrightarrow$ **Found:** *Black Wireless Earphones* (Library) $\rightarrow$ **100% Match Confidence**
2. **Lost:** *College ID Card* (Canteen) $\leftrightarrow$ **Found:** *Student ID Card* (Canteen) $\rightarrow$ **100% Match Confidence**
3. **Lost:** *Navy Blue Laptop Backpack* (Hostel Block B) $\rightarrow$ Ready for new matching submissions.
4. **Found:** *Brass Carabiner Keychain* (Dining Hall) $\rightarrow$ Ready for ownership claims.

---

## 📄 License
MIT License &copy; 2026 **LostLink** — AI-Powered Campus Lost & Found.
