from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, User, Team, ScrimMatch, Tournament, TournamentRegistration, AuditLog
from app.utils.security import admin_required, compute_audit_hash

admin_bp = Blueprint('admin', __name__)

def _record_admin_audit(actor_id, action, target_type, target_id, details=None):
    """Helper to append an audit log with SHA-256 chaining for admin actions."""
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

@admin_bp.before_request
def require_admin():
    if not current_user.is_authenticated:
        _record_admin_audit(None, 'ANONYMOUS_ADMIN_PROBE', 'AdminPortal', request.path, f"Anonymous visitor blocked from accessing {request.path}")
        flash('Please sign in to access this page.', 'warning')
        return redirect(url_for('auth.login', next=request.url))
    if current_user.role != 'ADMIN':
        _record_admin_audit(current_user.id, 'UNAUTHORIZED_ADMIN_ACCESS', 'AdminPortal', request.path, f"User {current_user.email} (role {current_user.role}) denied access to {request.path}")
        flash('Access denied: You do not have permission to view this resource.', 'danger')
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/')
def dashboard():
    total_users = User.query.count()
    total_teams = Team.query.count()
    total_scrims = ScrimMatch.query.count()
    total_tournaments = Tournament.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        stats={
            'users': total_users,
            'teams': total_teams,
            'scrims': total_scrims,
            'tournaments': total_tournaments
        },
        recent_users=recent_users,
        recent_audits=recent_audits
    )

@admin_bp.route('/users')
def users():
    search = request.args.get('q', '').strip()
    query = User.query
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.display_name.ilike(f'%{search}%')) |
            (User.mlbb_ign.ilike(f'%{search}%'))
        )
    user_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=user_list, search=search)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'ADMIN' or user_id == current_user.id:
        flash('You cannot modify the Administrator account status.', 'danger')
        return redirect(url_for('admin.users'))

    user.status = 'BANNED' if user.status == 'ACTIVE' else 'ACTIVE'
    db.session.commit()
    _record_admin_audit(current_user.id, 'USER_STATUS_CHANGE', 'User', user.id, f"Toggled status of {user.display_name} to {user.status}")
    flash(f'User {user.display_name} status updated to {user.status}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/change-role', methods=['POST'])
def change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'ADMIN' or user_id == current_user.id:
        flash('The exclusive Administrator account role cannot be modified.', 'danger')
        return redirect(url_for('admin.users'))

    new_role = request.form.get('role', 'PLAYER').strip().upper()
    if new_role == 'ADMIN':
        flash('Cannot promote to Administrator. The platform enforces a single dedicated Administrator account.', 'danger')
        return redirect(url_for('admin.users'))

    if new_role not in ['PLAYER', 'CAPTAIN']:
        flash('Invalid role. Student roles can only be toggled between Captain and Player.', 'danger')
        return redirect(url_for('admin.users'))

    old_role = user.role
    user.role = new_role
    db.session.commit()
    _record_admin_audit(current_user.id, 'USER_ROLE_CHANGE', 'User', user.id, f"Changed role of {user.display_name} from {old_role} to {new_role}")
    flash(f"User {user.display_name}'s role updated to {new_role}.", 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/tournaments/create', methods=['GET', 'POST'])
def create_tournament():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        game_title = request.form.get('game_title', 'Mobile Legends: Bang Bang')
        rules = request.form.get('rules', '').strip()
        tournament_format = request.form.get('format', 'SINGLE_ELIMINATION')
        max_teams = int(request.form.get('max_teams', 16))
        rank_tier_req = request.form.get('rank_tier_req', 'EPIC')
        reg_open_str = request.form.get('registration_open')
        reg_close_str = request.form.get('registration_close')

        if not title:
            flash('Tournament title is required.', 'danger')
            return render_template('admin/tournament_create.html')

        try:
            reg_open = datetime.fromisoformat(reg_open_str) if reg_open_str else datetime.utcnow()
            reg_close = datetime.fromisoformat(reg_close_str) if reg_close_str else datetime.utcnow() + timedelta(days=14)
        except ValueError:
            reg_open = datetime.utcnow()
            reg_close = datetime.utcnow() + timedelta(days=14)

        t = Tournament(
            title=title,
            description=description,
            game_title=game_title,
            rules=rules,
            format=tournament_format,
            max_teams=max_teams,
            rank_tier_req=rank_tier_req,
            registration_open=reg_open,
            registration_close=reg_close,
            status='REGISTRATION_OPEN',
            created_by_id=current_user.id
        )
        db.session.add(t)
        db.session.commit()

        flash(f'Tournament "{title}" published successfully!', 'success')
        return redirect(url_for('tournaments.detail', tournament_id=t.id))

    return render_template('admin/tournament_create.html')

@admin_bp.route('/audit-logs')
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template('admin/audit.html', logs=logs)
