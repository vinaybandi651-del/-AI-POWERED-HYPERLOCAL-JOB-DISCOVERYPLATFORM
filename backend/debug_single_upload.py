"""Single upload test - verify file written to disk."""
import sys, os, json, struct, zlib
from io import BytesIO

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from app import create_app
from database.db import query_db
from utils.security import create_access_token
from config import BASE_DIR

app = create_app()
upload_dir = os.path.join(BASE_DIR, 'uploads', 'avatars')

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

    png = make_png()
    r = c.post(
        '/api/users/avatar',
        headers=hdrs,
        data={'avatar': (BytesIO(png), 'photo.png', 'image/png')},
        content_type='multipart/form-data'
    )
    d = json.loads(r.data)
    print(f'Upload HTTP status : {r.status_code}')
    print(f'Response           : {d}')

    if d.get('avatar_url'):
        fname = d['avatar_url'].split('/api/users/avatar/')[-1]
        fpath = os.path.join(upload_dir, fname)
        exists = os.path.isfile(fpath)
        size = os.path.getsize(fpath) if exists else 0
        print(f'File on disk       : {fpath}')
        print(f'Exists             : {exists}')
        print(f'Size               : {size} bytes')

        # Serve it back
        r2 = c.get(d['avatar_url'])
        print(f'Serve status       : {r2.status_code} ({len(r2.data)} bytes)')
        print(f'Content-Type       : {r2.headers.get("Content-Type")}')

        if exists and r2.status_code == 200:
            print('\n>>> UPLOAD + SERVE: WORKING CORRECTLY <<<')
        else:
            print('\n>>> PROBLEM DETECTED <<<')
