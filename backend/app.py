import os
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import Config
from extensions import db, cors
try:
    import models
except Exception:
    models = None
from database.db import init_db
from database.seed_data import seed_database
from routes import (
    auth_bp,
    students_bp,
    employers_bp,
    jobs_bp,
    applications_bp,
    saved_jobs_bp,
    chat_bp,
    notifications_bp,
    recommendations_bp,
    admin_bp,
    reviews_bp,
    users_bp
)

def create_app(config_class=Config):
    frontend_dir = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    app.config.from_object(config_class)

    cors.init_app(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Register API Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(employers_bp, url_prefix='/api/employers')
    app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    app.register_blueprint(saved_jobs_bp, url_prefix='/api/saved_jobs')
    app.register_blueprint(saved_jobs_bp, url_prefix='/api/saved-jobs', name='saved_jobs_hyphen')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(chat_bp, url_prefix='/api/messages', name='messages_alias')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(reviews_bp, url_prefix='/api/reviews')
    app.register_blueprint(users_bp, url_prefix='/api/users')



    # Frontend routes
    @app.route('/')
    def serve_index():
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        target = os.path.join(frontend_dir, path)
        if os.path.exists(target):
            return send_from_directory(frontend_dir, path)
        # Check if html extension omitted
        if os.path.exists(target + '.html'):
            return send_from_directory(frontend_dir, path + '.html')
        return send_from_directory(frontend_dir, 'index.html')

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

    return app

if __name__ == '__main__':
    print("=" * 60)
    print("Initializing HyperLocal Job Match Backend Engine...")
    print("=" * 60)
    
    # Initialize and seed database if necessary
    init_db()
    seed_database()

    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"\n[*] HyperLocal Job Match Server running at http://127.0.0.1:{port}")
    print("[*] AI Recommendation Engine & Geo-matching active")
    print("[*] Demo users loaded. Ready for viva presentation!\n")
    app.run(host='0.0.0.0', port=port, debug=False)
