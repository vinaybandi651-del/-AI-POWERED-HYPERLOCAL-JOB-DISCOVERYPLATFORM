import os
import sys
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(BASE_DIR, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load backend/app.py directly to avoid root filename collision
backend_app_path = os.path.join(backend_dir, 'app.py')
spec = importlib.util.spec_from_file_location("backend_app_module", backend_app_path)
backend_app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_app_module)
create_app = backend_app_module.create_app

from database.db import init_db
from database.seed_data import seed_database

if __name__ == '__main__':
    print("=" * 60)
    print("Starting HyperLocal Job Match Server...")
    print("=" * 60)
    init_db()
    seed_database()

    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"\n[*] HyperLocal Job Match Server running at: http://127.0.0.1:{port}")
    print("[*] AI Recommendation Engine & Geo-matching active\n")
    app.run(host='0.0.0.0', port=port, debug=False)
