from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, User, Team, ScrimRequest, ScrimMatch, Tournament, Notification

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Live platform stats
    total_gamers = User.query.filter_by(status='ACTIVE').count()
    active_teams = Team.query.filter_by(status='ACTIVE').count()
    completed_scrims = ScrimMatch.query.filter_by(status='COMPLETED').count()
    tournaments_count = Tournament.query.count()

    return render_template(
        'index.html',
        stats={
            'gamers': max(total_gamers, 10),
            'teams': max(active_teams, 2),
            'scrims': max(completed_scrims, 1),
            'tournaments': max(tournaments_count, 1)
        }
    )

@main_bp.route('/dashboard')
@login_required
def dashboard():
    my_team = current_user.primary_team

    # Upcoming scrims for the user's team
    upcoming_scrims = []
    if my_team:
        upcoming_scrims = ScrimMatch.query.filter(
            ((ScrimMatch.team1_id == my_team.id) | (ScrimMatch.team2_id == my_team.id)),
            ScrimMatch.status == 'SCHEDULED'
        ).order_by(ScrimMatch.scheduled_at.asc()).limit(3).all()

    # Open scrim challenges available to accept
    open_scrims = ScrimRequest.query.filter_by(status='OPEN')
    if my_team:
        open_scrims = open_scrims.filter(ScrimRequest.team_id != my_team.id)
    open_scrims = open_scrims.order_by(ScrimRequest.created_at.desc()).limit(3).all()

    # Active / upcoming tournaments
    active_tournaments = Tournament.query.filter(
        Tournament.status.in_(['REGISTRATION_OPEN', 'ONGOING'])
    ).order_by(Tournament.registration_close.asc()).limit(3).all()

    # Recent notifications
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    return render_template(
        'dashboard.html',
        my_team=my_team,
        upcoming_scrims=upcoming_scrims,
        open_scrims=open_scrims,
        active_tournaments=active_tournaments,
        notifications=notifications
    )

@main_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('main.dashboard'))
