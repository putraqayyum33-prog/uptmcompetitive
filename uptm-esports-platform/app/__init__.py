import os
from flask import Flask
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from app.models import db, User, Notification

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder exists for SQLite
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Global Context Processors
    @app.context_processor
    def inject_global_vars():
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False
            ).count()
        return {
            'unread_notifications_count': unread_count,
            'app_name': 'UPTM Esports Platform'
        }

    # Template Filters
    @app.template_filter('format_datetime')
    def format_datetime(value, fmt='%d %b %Y, %I:%M %p'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('format_date')
    def format_date(value, fmt='%d %b %Y'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('rank_badge_class')
    def rank_badge_class(tier):
        tier_map = {
            'WARRIOR': 'badge-warrior',
            'ELITE': 'badge-elite',
            'MASTER': 'badge-master',
            'GRANDMASTER': 'badge-grandmaster',
            'EPIC': 'badge-epic',
            'LEGEND': 'badge-legend',
            'MYTHIC': 'badge-mythic',
            'MYTHICAL_HONOR': 'badge-honor',
            'MYTHICAL_GLORY': 'badge-glory',
            'MYTHICAL_IMMORTAL': 'badge-immortal'
        }
        return tier_map.get(tier, 'badge-secondary')

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.teams import teams_bp
    from app.routes.scrims import scrims_bp
    from app.routes.tournaments import tournaments_bp
    from app.routes.leaderboard import leaderboard_bp
    from app.routes.profile import profile_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(teams_bp, url_prefix='/teams')
    app.register_blueprint(scrims_bp, url_prefix='/scrims')
    app.register_blueprint(tournaments_bp, url_prefix='/tournaments')
    app.register_blueprint(leaderboard_bp, url_prefix='/leaderboard')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
