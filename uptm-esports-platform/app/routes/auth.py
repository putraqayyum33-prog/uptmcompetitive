from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from app.models import db, User, AuditLog
from app.utils.security import is_allowed_uptm_email, compute_audit_hash

auth_bp = Blueprint('auth', __name__)

def _record_audit_log(actor_id, action, target_type, target_id, details=None):
    """Helper to append an audit log with SHA-256 chaining."""
    last_log = AuditLog.query.order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.hash if last_log else "GENESIS_HASH_UPTM_ESPORTS_2026"
    now_str = datetime.utcnow().isoformat()
    ip_addr = request.remote_addr or "127.0.0.1"
    
    actor_str = str(actor_id) if actor_id is not None else "ANONYMOUS"
    log_hash = compute_audit_hash(
        actor_str, action, target_type, str(target_id), prev_hash, now_str
    )
    
    audit_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        details=details,
        ip_address=ip_addr,
        previous_hash=prev_hash,
        hash=log_hash,
        created_at=datetime.utcnow()
    )
    db.session.add(audit_entry)
    db.session.commit()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    active_tab = request.args.get('tab', 'STUDENT')

    if request.method == 'POST':
        form_type = request.form.get('form_type', 'STUDENT')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if form_type == 'ADMIN':
            active_tab = 'ADMIN'
            if email == Config.ADMIN_EMAIL.lower() and password == Config.ADMIN_PASSWORD:
                admin_user = User.query.filter_by(email=Config.ADMIN_EMAIL.lower()).first()
                if not admin_user:
                    admin_user = User(
                        email=Config.ADMIN_EMAIL.lower(),
                        display_name='System Administrator',
                        role='ADMIN',
                        status='ACTIVE',
                        mlbb_ign='UPTM_Admin',
                        mlbb_id='100000001',
                        rank_tier='MYTHICAL_IMMORTAL'
                    )
                    admin_user.set_password(Config.ADMIN_PASSWORD)
                    db.session.add(admin_user)
                    db.session.commit()

                login_user(admin_user)
                _record_audit_log(admin_user.id, 'ADMIN_LOGIN', 'User', admin_user.id, 'Admin login successful')
                flash('Welcome back, System Administrator!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                _record_audit_log(None, 'ANONYMOUS_ADMIN_LOGIN_FAILED', 'AdminPortal', '0', f"Failed admin login attempt with identifier '{email}'")
                flash('Invalid Administrator credentials.', 'danger')
        else:
            # Student Login
            if not email or not password:
                flash('Email and password are required.', 'danger')
            else:
                user = User.query.filter_by(email=email).first()
                if user and user.check_password(password):
                    if user.status == 'BANNED':
                        _record_audit_log(user.id, 'SUSPENDED_LOGIN_BLOCKED', 'User', user.id, f"Suspended account {user.email} attempted login")
                        flash('Your account has been suspended. Please contact UPTM Esports Club.', 'danger')
                        return render_template('auth/login.html', active_tab=active_tab)

                    login_user(user)
                    _record_audit_log(user.id, 'USER_LOGIN', 'User', user.id, 'Student login successful')
                    flash(f'Welcome back, {user.display_name}!', 'success')
                    next_page = request.args.get('next')
                    return redirect(next_page or url_for('main.dashboard'))
                else:
                    _record_audit_log(None, 'ANONYMOUS_LOGIN_FAILED', 'User', email, f"Failed student login attempt for email '{email}'")
                    flash('Invalid institutional email or password.', 'danger')

    return render_template('auth/login.html', active_tab=active_tab)

@auth_bp.route('/auth/demo-login/<role>')
def demo_login(role):
    """1-Click Fast Login for FYP presentation & evaluation."""
    role = role.upper()
    user = None
    if role == 'ADMIN':
        user = User.query.filter_by(role='ADMIN').first()
    elif role == 'CAPTAIN':
        user = User.query.filter_by(role='CAPTAIN').first()
    else:
        user = User.query.filter_by(role='PLAYER').first()

    if user:
        login_user(user)
        _record_audit_log(user.id, 'DEMO_LOGIN', 'User', user.id, f'Demo 1-click login as {role}')
        flash(f'Logged in as {user.display_name} ({user.role})', 'info')
        if user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.dashboard'))

    flash(f'Demo user for {role} not found. Please run seed.py first.', 'warning')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        display_name = request.form.get('display_name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        phone = request.form.get('phone', '').strip()
        mlbb_ign = request.form.get('mlbb_ign', '').strip()
        mlbb_id = request.form.get('mlbb_id', '').strip()
        rank_tier = request.form.get('rank_tier', 'EPIC')

        # Institutional Domain Validation
        if not is_allowed_uptm_email(email):
            flash('Only UPTM institutional emails (@student.uptm.edu.my or @uptm.edu.my) are allowed.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this institutional email already exists.', 'warning')
            return redirect(url_for('auth.login'))

        # Create new student gamer account
        new_user = User(
            email=email,
            display_name=display_name or mlbb_ign or email.split('@')[0],
            mlbb_ign=mlbb_ign,
            mlbb_id=mlbb_id,
            rank_tier=rank_tier,
            role='PLAYER',
            status='ACTIVE'
        )
        new_user.set_password(password)
        if student_id:
            new_user.student_id = student_id
        if phone:
            new_user.phone = phone

        db.session.add(new_user)
        db.session.commit()

        _record_audit_log(new_user.id, 'USER_REGISTER', 'User', new_user.id, 'Institutional registration')

        login_user(new_user)
        flash('Registration successful! Welcome to the UPTM Esports Platform.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    _record_audit_log(user_id, 'USER_LOGOUT', 'User', user_id, 'User logged out')
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('main.index'))
