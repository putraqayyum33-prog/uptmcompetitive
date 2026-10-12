from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, Team, TeamMember, User, Notification, ScrimMatch

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/')
def index():
    search = request.args.get('q', '').strip()
    query = Team.query.filter_by(status='ACTIVE')
    if search:
        query = query.filter(
            (Team.name.ilike(f'%{search}%')) | (Team.tag.ilike(f'%{search}%'))
        )
    teams = query.order_by(Team.created_at.desc()).all()
    return render_template('teams/index.html', teams=teams, search=search)

@teams_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Verify user does not already lead an active team
    existing_captained = Team.query.filter_by(captain_id=current_user.id, status='ACTIVE').first()
    if existing_captained:
        flash('You are already the captain of an active team.', 'warning')
        return redirect(url_for('teams.detail', team_id=existing_captained.id))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        tag = request.form.get('tag', '').strip().upper()
        description = request.form.get('description', '').strip()
        logo_url = request.form.get('logo_url', '').strip()

        if not name or not tag:
            flash('Team name and team tag are required.', 'danger')
            return render_template('teams/create.html')

        if len(tag) > 6:
            flash('Team tag cannot exceed 6 characters.', 'danger')
            return render_template('teams/create.html')

        if Team.query.filter((Team.name == name) | (Team.tag == tag)).first():
            flash('A team with this name or tag already exists.', 'danger')
            return render_template('teams/create.html')

        # Create new team
        if not logo_url:
            logo_url = f"https://api.dicebear.com/7.x/identicon/svg?seed={tag}"

        team = Team(
            name=name,
            tag=tag,
            description=description,
            logo_url=logo_url,
            captain_id=current_user.id,
            status='ACTIVE'
        )
        db.session.add(team)
        db.session.flush()

        # Add captain as team member
        member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role='CAPTAIN',
            status='ACTIVE'
        )
        db.session.add(member)

        if current_user.role == 'PLAYER':
            current_user.role = 'CAPTAIN'

        db.session.commit()
        flash(f'Team "{team.name} [{team.tag}]" created successfully!', 'success')
        return redirect(url_for('teams.detail', team_id=team.id))

    return render_template('teams/create.html')

@teams_bp.route('/<int:team_id>')
def detail(team_id):
    team = Team.query.get_or_404(team_id)
    members = TeamMember.query.filter_by(team_id=team.id).all()
    
    # Recent match history
    matches = ScrimMatch.query.filter(
        ((ScrimMatch.team1_id == team.id) | (ScrimMatch.team2_id == team.id))
    ).order_by(ScrimMatch.scheduled_at.desc()).limit(10).all()

    is_captain = current_user.is_authenticated and current_user.id == team.captain_id
    is_member = current_user.is_authenticated and any(m.user_id == current_user.id for m in members)

    return render_template(
        'teams/detail.html',
        team=team,
        members=members,
        matches=matches,
        is_captain=is_captain,
        is_member=is_member
    )

@teams_bp.route('/<int:team_id>/invite', methods=['POST'])
@login_required
def invite_member(team_id):
    team = Team.query.get_or_404(team_id)
    if team.captain_id != current_user.id and not current_user.is_admin:
        abort(403)

    identifier = request.form.get('identifier', '').strip()
    target_user = User.query.filter(
        (User.email == identifier.lower()) | (User.mlbb_ign == identifier)
    ).first()

    if not target_user:
        flash(f'No registered UPTM gamer found matching "{identifier}".', 'danger')
        return redirect(url_for('teams.detail', team_id=team.id))

    # Check if user is already in this team
    existing = TeamMember.query.filter_by(team_id=team.id, user_id=target_user.id).first()
    if existing:
        flash(f'{target_user.display_name} is already a member of this team.', 'warning')
        return redirect(url_for('teams.detail', team_id=team.id))

    # Add member
    new_member = TeamMember(
        team_id=team.id,
        user_id=target_user.id,
        role='STARTER',
        status='ACTIVE'
    )
    db.session.add(new_member)

    # Send notification
    notif = Notification(
        user_id=target_user.id,
        title='Added to Team Roster',
        message=f'You have been added to the roster of {team.name} [{team.tag}]!',
        link=url_for('teams.detail', team_id=team.id)
    )
    db.session.add(notif)
    db.session.commit()

    flash(f'{target_user.display_name} has been added to {team.name}!', 'success')
    return redirect(url_for('teams.detail', team_id=team.id))

@teams_bp.route('/<int:team_id>/remove/<int:member_id>', methods=['POST'])
@login_required
def remove_member(team_id, member_id):
    team = Team.query.get_or_404(team_id)
    if team.captain_id != current_user.id and not current_user.is_admin:
        abort(403)

    member = TeamMember.query.filter_by(id=member_id, team_id=team.id).first_or_404()
    if member.user_id == team.captain_id:
        flash('The team captain cannot be removed from the team.', 'danger')
        return redirect(url_for('teams.detail', team_id=team.id))

    db.session.delete(member)
    db.session.commit()
    flash('Roster member removed.', 'info')
    return redirect(url_for('teams.detail', team_id=team.id))

@teams_bp.route('/<int:team_id>/leave', methods=['POST'])
@login_required
def leave_team(team_id):
    team = Team.query.get_or_404(team_id)
    member = TeamMember.query.filter_by(team_id=team.id, user_id=current_user.id).first_or_404()

    if team.captain_id == current_user.id:
        flash('Captains cannot leave without disbanding the team or transferring leadership.', 'danger')
        return redirect(url_for('teams.detail', team_id=team.id))

    db.session.delete(member)
    db.session.commit()
    flash(f'You have left {team.name}.', 'info')
    return redirect(url_for('main.dashboard'))
