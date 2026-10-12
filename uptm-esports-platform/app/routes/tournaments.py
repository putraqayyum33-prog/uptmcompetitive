from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, Tournament, TournamentRegistration, TournamentMatch, Team, Notification

tournaments_bp = Blueprint('tournaments', __name__)

@tournaments_bp.route('/')
def index():
    tournaments = Tournament.query.order_by(Tournament.created_at.desc()).all()
    return render_template('tournaments/index.html', tournaments=tournaments)

@tournaments_bp.route('/<int:tournament_id>')
def detail(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    registrations = TournamentRegistration.query.filter_by(tournament_id=tournament.id).all()
    matches = TournamentMatch.query.filter_by(tournament_id=tournament.id).order_by(
        TournamentMatch.round.asc(), TournamentMatch.match_number.asc()
    ).all()

    # Organize matches by round for bracket view
    rounds = {}
    for m in matches:
        rounds.setdefault(m.round, []).append(m)

    my_team = current_user.primary_team if current_user.is_authenticated else None
    is_registered = False
    if my_team:
        is_registered = any(r.team_id == my_team.id for r in registrations)

    return render_template(
        'tournaments/detail.html',
        tournament=tournament,
        registrations=registrations,
        rounds=rounds,
        my_team=my_team,
        is_registered=is_registered
    )

@tournaments_bp.route('/<int:tournament_id>/register', methods=['POST'])
@login_required
def register(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    my_team = current_user.primary_team

    if not my_team:
        flash('You must join or create a team to register for tournaments.', 'warning')
        return redirect(url_for('teams.create'))

    if my_team.captain_id != current_user.id and not current_user.is_admin:
        flash('Only team captains can register their roster for tournaments.', 'danger')
        return redirect(url_for('tournaments.detail', tournament_id=tournament.id))

    if tournament.status != 'REGISTRATION_OPEN':
        flash('Tournament registrations are currently closed.', 'warning')
        return redirect(url_for('tournaments.detail', tournament_id=tournament.id))

    # Check already registered
    existing = TournamentRegistration.query.filter_by(
        tournament_id=tournament.id, team_id=my_team.id
    ).first()
    if existing:
        flash('Your team is already registered for this tournament.', 'info')
        return redirect(url_for('tournaments.detail', tournament_id=tournament.id))

    reg_count = TournamentRegistration.query.filter_by(tournament_id=tournament.id).count()
    if reg_count >= tournament.max_teams:
        flash('Tournament has reached maximum team capacity.', 'danger')
        return redirect(url_for('tournaments.detail', tournament_id=tournament.id))

    new_reg = TournamentRegistration(
        tournament_id=tournament.id,
        team_id=my_team.id,
        seed=reg_count + 1,
        status='APPROVED'
    )
    db.session.add(new_reg)
    db.session.commit()

    flash(f'Team {my_team.name} has been successfully registered for {tournament.title}!', 'success')
    return redirect(url_for('tournaments.detail', tournament_id=tournament.id))
