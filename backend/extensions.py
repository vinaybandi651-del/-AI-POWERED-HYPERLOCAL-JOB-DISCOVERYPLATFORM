try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
except ImportError:
    class DummyDB:
        def init_app(self, app): pass
        def create_all(self): pass
    db = DummyDB()

from flask_cors import CORS
cors = CORS()

