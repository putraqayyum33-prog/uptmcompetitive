import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, ScrimRequest, ScrimMatch, Team, Notification

scrims_bp = Blueprint('scrims', __name__)

def _generate_room_credentials():
    room_id = f"UPTM-{random.randint(10000, 99999)}"
    password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return room_id, password

@scrims_bp.route('/')
def index():
    tier_filter = request.args.get('tier', '').strip()
    status_tab = request.args.get('tab', 'OPEN')

    if status_tab == 'SCHEDULED':
        matches_query = ScrimMatch.query.order_by(ScrimMatch.scheduled_at.desc())
        matches = matches_query.all()
        return render_template('scrims/index.html', matches=matches, status_tab=status_tab, tier_filter=tier_filter)

    # Open Requests
    query = ScrimRequest.query.filter_by(status='OPEN')
    if tier_filter:
        query = query.filter((ScrimRequest.rank_tier_min == tier_filter) | (ScrimRequest.rank_tier_max == tier_filter))

    scrim_requests = query.order_by(ScrimRequest.preferred_datetime.asc()).all()
    return render_template('scrims/index.html', requests=scrim_requests, status_tab=status_tab, tier_filter=tier_filter)

@scrims_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    my_team = current_user.primary_team
    if not my_team:
        flash('You must join or create a team before requesting a scrim match.', 'warning')
        return redirect(url_for('teams.create'))

    if request.method == 'POST':
        match_format = request.form.get('format', 'BO3')
        rank_min = request.form.get('rank_tier_min', 'EPIC')
        rank_max = request.form.get('rank_tier_max', 'MYTHIC')
        preferred_dt_str = request.form.get('preferred_datetime')
        notes = request.form.get('notes', '').strip()

        if not preferred_dt_str:
            flash('Preferred date and time is required.', 'danger')
            return render_template('scrims/create.html', my_team=my_team)

        try:
            preferred_datetime = datetime.fromisoformat(preferred_dt_str)
        except ValueError:
            preferred_datetime = datetime.utcnow() + timedelta(days=1)

        scrim = ScrimRequest(
            team_id=my_team.id,
            requested_by_id=current_user.id,
            game_title='Mobile Legends: Bang Bang',
            format=match_format,
            rank_tier_min=rank_min,
            rank_tier_max=rank_max,
            preferred_datetime=preferred_datetime,
            notes=notes,
            status='OPEN'
        )
        db.session.add(scrim)
        db.session.commit()

        flash('Scrim request posted to the lobby! Other teams can now accept your challenge.', 'success')
        return redirect(url_for('scrims.index'))

    return render_template('scrims/create.html', my_team=my_team)

@scrims_bp.route('/<int:request_id>/accept', methods=['POST'])
@login_required
def accept(request_id):
    scrim_req = ScrimRequest.query.get_or_404(request_id)
    my_team = current_user.primary_team

    if not my_team:
        flash('You must have an active team to accept a scrim challenge.', 'warning')
        return redirect(url_for('teams.create'))

    if my_team.id == scrim_req.team_id:
        flash('You cannot accept your own team\'s scrim request.', 'warning')
        return redirect(url_for('scrims.index'))

    if scrim_req.status != 'OPEN':
        flash('This scrim challenge has already been matched or closed.', 'warning')
        return redirect(url_for('scrims.index'))

    # Generate MLBB custom room credentials
    room_id, room_pw = _generate_room_credentials()

    match = ScrimMatch(
        request_id=scrim_req.id,
        team1_id=scrim_req.team_id,
        team2_id=my_team.id,
        match_room_id=room_id,
        match_room_password=room_pw,
        scheduled_at=scrim_req.preferred_datetime,
        status='SCHEDULED'
    )
    scrim_req.status = 'MATCHED'
    db.session.add(match)

    # Notify requester
    notif1 = Notification(
        user_id=scrim_req.requested_by_id,
        title='Scrim Challenge Accepted!',
        message=f'Team {my_team.name} has accepted your scrim challenge! Room details generated.',
        link=url_for('scrims.match_detail', match_id=match.id)
    )
    db.session.add(notif1)
    db.session.commit()

    flash('Scrim challenge confirmed! Private match room credentials generated.', 'success')
    return redirect(url_for('scrims.match_detail', match_id=match.id))

@scrims_bp.route('/match/<int:match_id>')
@login_required
def match_detail(match_id):
    match = ScrimMatch.query.get_or_404(match_id)
    my_team = current_user.primary_team

    is_participant = (
        current_user.is_admin or
        (my_team and (my_team.id in [match.team1_id, match.team2_id]))
    )

    return render_template(
        'scrims/detail.html',
        match=match,
        is_participant=is_participant
    )

@scrims_bp.route('/match/<int:match_id>/report', methods=['POST'])
@login_required
def report_result(match_id):
    match = ScrimMatch.query.get_or_404(match_id)
    my_team = current_user.primary_team

    if not current_user.is_admin and (not my_team or my_team.id not in [match.team1_id, match.team2_id]):
        abort(403)

    team1_score = int(request.form.get('team1_score', 0))
    team2_score = int(request.form.get('team2_score', 0))
    winner_team_id = request.form.get('winner_id')
    screenshot_url = request.form.get('screenshot_url', '').strip()

    match.team1_score = team1_score
    match.team2_score = team2_score
    if winner_team_id:
        match.winner_id = int(winner_team_id)
    elif team1_score > team2_score:
        match.winner_id = match.team1_id
    elif team2_score > team1_score:
        match.winner_id = match.team2_id

    match.screenshot_url = screenshot_url
    match.status = 'COMPLETED'
    db.session.commit()

    flash('Match result successfully reported and verified!', 'success')
    return redirect(url_for('scrims.match_detail', match_id=match.id))
