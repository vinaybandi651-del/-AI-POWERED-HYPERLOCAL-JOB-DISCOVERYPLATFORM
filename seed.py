import sys
import os

# Ensure backend directory is in python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from database.seed_data import seed_database

if __name__ == '__main__':
    force = '--force' in sys.argv or '-f' in sys.argv or True
    print("=" * 60)
    print("Seeding HyperLocal Job Match Database...")
    print("=" * 60)
    seed_database(force=force)
    print("\nDatabase seeding completed successfully!")
