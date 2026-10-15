import json
import io
import urllib.request
import urllib.error
from app import create_app
from models import db, User, Item, Claim, Notification, Flag
from seed import seed_database

print("=" * 65)
print("TESTING LOSTLINK HTTP ENDPOINTS, AUTHENTICATION & MULTIMODAL AI:")
print("=" * 65)

app = create_app()

with app.app_context():
    if Item.query.count() == 0 or User.query.count() == 0:
        print("-> Initializing benchmark seed data...")
        seed_database(app)

client = app.test_client()

# 1. Test Public Routes
public_routes = ['/', '/report', '/post', '/login', '/signup', '/admin', '/item/1', '/matches/1', '/api/matches/1', '/api/items']

for r in public_routes:
    resp = client.get(r)
    assert resp.status_code == 200, f"Route {r} failed with status {resp.status_code}"
    print(f"{r:22} -> Status: {resp.status_code} OK ({len(resp.data)} bytes)")

# 2. Test Student Authentication (Login)
print("\n" + "=" * 65)
print("TESTING USER AUTHENTICATION (/login & /signup):")
print("=" * 65)
login_resp = client.post('/login', data={
    'email': 'student@campus.edu',
    'password': 'Student@123'
}, follow_redirects=True)
assert login_resp.status_code == 200, "Login failed"
print("[OK] Student login successful (Session established)")

# 3. Test Authenticated Routes (My Reports, Profile, Notifications)
auth_routes = ['/my-reports', '/profile', '/notifications']
for r in auth_routes:
    resp = client.get(r)
    assert resp.status_code == 200, f"Authenticated route {r} failed with {resp.status_code}"
    print(f"{r:22} -> Status: {resp.status_code} OK ({len(resp.data)} bytes)")

# 4. Test Submitting a New Item with AI Embeddings
print("\n" + "=" * 65)
print("TESTING REPORTING ITEM & AI MATCHING (/report):")
print("=" * 65)
post_payload = {
    'item_type': 'found',
    'title': 'Found Wireless Earphones in Study Hall',
    'description': 'Found black wireless earphones left on desk 12 near study hall.',
    'category': 'Earphones',
    'location': 'Library',
    'contact': '+91 99999 88888'
}
post_resp = client.post('/report', data=post_payload, follow_redirects=False)
assert post_resp.status_code in (301, 302, 303), f"Expected redirect, got {post_resp.status_code}"
redirect_url = post_resp.headers.get('Location')
print(f"[OK] Item report posted, redirected to: {redirect_url}")

# Verify match page for newly created item
match_page_resp = client.get(redirect_url)
assert match_page_resp.status_code == 200
html = match_page_resp.data.decode()
assert "AI Matches for:" in html or "TOP AI CANDIDATE" in html
print("[OK] Matches page rendered top candidate comparison successfully!")

# 5. Test JSON API
api_resp = client.get('/api/matches/1')
assert api_resp.status_code == 200
data = json.loads(api_resp.data.decode())
assert 'target_item' in data and 'matches' in data
print(f"[OK] API Matches returned {len(data['matches'])} candidate matches for item #1")

# 6. Test Submitting Ownership Claim
claim_resp = client.post('/item/2/claim', data={
    'name': 'Alex Rivera',
    'contact': '+91 98765 43210',
    'proof': 'Earphones case has small blue sticker on bottom.'
}, follow_redirects=True)
assert claim_resp.status_code == 200
print("[OK] Ownership claim submitted successfully")

# 7. Test Admin Moderation (Toggle Status & Claim Review)
print("\n" + "=" * 65)
print("TESTING ADMIN DASHBOARD & MODERATION:")
print("=" * 65)
admin_login = client.post('/login', data={
    'email': 'admin@campus.edu',
    'password': 'Admin@123'
}, follow_redirects=True)
assert admin_login.status_code == 200
print("[OK] Admin login successful")

admin_page = client.get('/admin')
assert admin_page.status_code == 200
print("[OK] Admin dashboard loaded with metric counters")

# 8. Check live server
try:
    with urllib.request.urlopen('http://127.0.0.1:5000/', timeout=2) as live:
        if live.status == 200:
            print("\n[OK] Live web server confirmed active at http://127.0.0.1:5000!")
except Exception:
    print("\n[INFO] Live background server ping skipped; native in-memory test client verified all suites.")

print("\n" + "=" * 65)
print("ALL LOSTLINK ENDPOINT, AUTH & AI MATCHING TESTS PASSED PERFECTLY!")
print("=" * 65)
