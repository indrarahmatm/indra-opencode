import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///entokmart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Database Connection Pool (for production with PostgreSQL)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
# JSON optimization
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Security Headers (WAF-like protection)
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; img-src 'self' data: https:; font-src 'self' https: data:;"
    return response

# Login rate limiting
app.config['LOGIN_DISABLED'] = False

app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@entokmart.com')

# RajaOngkir API
app.config['RAJAONGKIR_API_KEY'] = 'GVcELgoo900bfa223a9d68a4IAn4c8Rx'
app.config['RAJAONGKIR_BASE_URL'] = 'https://rajaongkir.komerce.id/api/v1'

# Midtrans Payment Gateway
app.config['MIDTRANS_SERVER_KEY'] = os.environ.get('MIDTRANS_SERVER_KEY', '')
app.config['MIDTRANS_CLIENT_KEY'] = os.environ.get('MIDTRANS_CLIENT_KEY', '')
app.config['MIDTRANS_IS_PRODUCTION'] = os.environ.get('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'
app.config['MIDTRANS_SNAP_URL'] = 'https://app.snap-midtrans.com/snap/v1'
app.config['MIDTRANS_API_URL'] = 'https://api.midtrans.com/v2'

# Rate limiting
app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
app.config['RATELIMIT_STRATEGY'] = 'fixed-window'
app.config['RATELIMIT_DEFAULT'] = '200 per day'
app.config['RATELIMIT_HEADERS_ENABLED'] = True

# Performance Optimization - Caching
app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes default
app.config['CACHE_THRESHOLD'] = 500  # Max 500 items cached

mail = Mail(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20000 per day", "5000 per hour"],
    storage_uri="memory://",
    enabled=False,
)

# Initialize cache
cache = Cache(app)

# Initialize compression for faster response
Compress(app)
Compress.init_app(app, {
    'gzip_level': 6,
    'gzip_ignore': ['text/html'],
})

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from models import db, User, Category
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from routes import *

@app.template_filter('format_number')
def format_number(value):
    if value is None:
        return "0"
    return "{:,}".format(int(value))

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5003))
    with app.app_context():
        db.create_all()
        Category.get_default_categories()
    app.run(debug=debug, port=port, use_reloader=False, host='0.0.0.0')