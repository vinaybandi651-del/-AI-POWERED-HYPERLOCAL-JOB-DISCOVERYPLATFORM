import sys, os, json, struct, zlib
from io import BytesIO

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import create_app
from database.db import query_db
from utils.security import create_access_token
from config import BASE_DIR

app = create_app()

print("=== Registered /api/users routes ===")
with app.app_context():
    for rule in app.url_map.iter_rules():
        if 'users' in str(rule):
            print(f"  {sorted(rule.methods)} {rule}")

upload_dir = os.path.join(BASE_DIR, 'uploads', 'avatars')
print(f"\nUpload dir : {upload_dir}")
print(f"Exists     : {os.path.exists(upload_dir)}")
os.makedirs(upload_dir, exist_ok=True)
print(f"Writable   : {os.access(upload_dir, os.W_OK)}")

def make_png():
    sig = b'\x89PNG\r\n\x1a\n'
    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        return c + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00'))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

with app.test_client() as c:
    student = query_db(
        "SELECT id, email, role, full_name FROM users WHERE role='student' LIMIT 1",
        (), one=True
    )
    token = create_access_token(
        student['id'], student['email'], student['role'], student['full_name']
    )
    hdrs = {'Authorization': 'Bearer ' + token}

    print(f"\nStudent: {student['email']} (id={student['id']})")

    # 1. Auth check
    r = c.get('/api/users/profile', headers=hdrs)
    print(f"\n1. GET /api/users/profile -> {r.status_code}")
    d = json.loads(r.data)
    print(f"   avatar_url = {d.get('user',{}).get('avatar_url')}")

    # 2. Upload with 'avatar' field name (what browser sends)
    png = make_png()
    r2 = c.post(
        '/api/users/avatar',
        headers=hdrs,
        data={'avatar': (BytesIO(png), 'photo.png', 'image/png')},
        content_type='multipart/form-data'
    )
    d2 = json.loads(r2.data)
    print(f"\n2. POST /api/users/avatar (field=avatar) -> {r2.status_code}")
    print(f"   Response: {d2}")

    # 3. Upload with 'file' field name (alternative)
    r3 = c.post(
        '/api/users/avatar',
        headers=hdrs,
        data={'file': (BytesIO(png), 'photo.png', 'image/png')},
        content_type='multipart/form-data'
    )
    d3 = json.loads(r3.data)
    print(f"\n3. POST /api/users/avatar (field=file) -> {r3.status_code}")
    print(f"   Response: {d3}")

    # 4. Check the file was actually saved on disk
    if d2.get('avatar_url'):
        fname = d2['avatar_url'].split('/api/users/avatar/')[-1]
        fpath = os.path.join(upload_dir, fname)
        print(f"\n4. File on disk: {fpath}")
        print(f"   Exists: {os.path.isfile(fpath)}")
        if os.path.isfile(fpath):
            print(f"   Size  : {os.path.getsize(fpath)} bytes")

    # 5. Serve the avatar
    if d2.get('avatar_url'):
        r5 = c.get(d2['avatar_url'])
        print(f"\n5. GET {d2['avatar_url']} -> {r5.status_code} ({len(r5.data)} bytes)")
        ct = r5.headers.get('Content-Type','?')
        print(f"   Content-Type: {ct}")

    # 6. Verify profile now has avatar_url
    r6 = c.get('/api/users/profile', headers=hdrs)
    d6 = json.loads(r6.data)
    print(f"\n6. GET /api/users/profile (after upload) -> {r6.status_code}")
    print(f"   avatar_url = {d6.get('user',{}).get('avatar_url')}")

    # 7. DELETE avatar
    r7 = c.delete('/api/users/avatar', headers=hdrs)
    d7 = json.loads(r7.data)
    print(f"\n7. DELETE /api/users/avatar -> {r7.status_code}")
    print(f"   Response: {d7}")

    print("\n=== DONE ===")
