from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from app.utils.security import encrypt_pii, decrypt_pii

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    
    # Encrypted PII fields (AES-256)
    student_id_enc = db.Column(db.String(255), nullable=True)
    phone_enc = db.Column(db.String(255), nullable=True)
    
    # MLBB Player Attributes
    mlbb_ign = db.Column(db.String(50), nullable=True)
    mlbb_id = db.Column(db.String(30), nullable=True)
    rank_tier = db.Column(db.String(30), default='EPIC', index=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    # Role & Status
    role = db.Column(db.String(20), default='PLAYER', index=True) # ADMIN, CAPTAIN, PLAYER
    status = db.Column(db.String(20), default='ACTIVE', index=True) # ACTIVE, BANNED, INACTIVE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team_memberships = db.relationship('TeamMember', back_populates='user', cascade='all, delete-orphan')
    captained_teams = db.relationship('Team', back_populates='captain', foreign_keys='Team.captain_id')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    created_tournaments = db.relationship('Tournament', back_populates='creator')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def student_id(self) -> str | None:
        return decrypt_pii(self.student_id_enc)

    @student_id.setter
    def student_id(self, val: str | None):
        self.student_id_enc = encrypt_pii(val)

    @property
    def phone(self) -> str | None:
        return decrypt_pii(self.phone_enc)

    @phone.setter
    def phone(self, val: str | None):
        self.phone_enc = encrypt_pii(val)

    @property
    def primary_team(self):
        """Get the user's current active team."""
        membership = next((m for m in self.team_memberships if m.status == 'ACTIVE'), None)
        return membership.team if membership else None

    @property
    def is_admin(self) -> bool:
        return self.role == 'ADMIN'

    @property
    def is_captain(self) -> bool:
        return self.role == 'CAPTAIN' or len(self.captained_teams) > 0


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    tag = db.Column(db.String(10), unique=True, nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    captain_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='ACTIVE', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    captain = db.relationship('User', back_populates='captained_teams', foreign_keys=[captain_id])
    members = db.relationship('TeamMember', back_populates='team', cascade='all, delete-orphan')
    scrim_requests = db.relationship('ScrimRequest', back_populates='team', cascade='all, delete-orphan')
    tournament_registrations = db.relationship('TournamentRegistration', back_populates='team', cascade='all, delete-orphan')

    @property
    def active_members(self):
        return [m for m in self.members if m.status == 'ACTIVE']

    @property
    def total_scrims_played(self):
        return ScrimMatch.query.filter(
            ((ScrimMatch.team1_id == self.id) | (ScrimMatch.team2_id == self.id)),
            ScrimMatch.status == 'COMPLETED'
        ).count()

    @property
    def scrim_wins(self):
        return ScrimMatch.query.filter_by(winner_id=self.id, status='COMPLETED').count()

    @property
    def win_rate(self) -> float:
        total = self.total_scrims_played
        if total == 0:
            return 0.0
        return round((self.scrim_wins / total) * 100, 1)


class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='MEMBER') # CAPTAIN, STARTER, SUB
    status = db.Column(db.String(20), default='ACTIVE') # ACTIVE, INVITED, PENDING
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', back_populates='members')
    user = db.relationship('User', back_populates='team_memberships')


class ScrimRequest(db.Model):
    __tablename__ = 'scrim_requests'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_title = db.Column(db.String(100), default='Mobile Legends: Bang Bang')
    rank_tier_min = db.Column(db.String(30), default='EPIC')
    rank_tier_max = db.Column(db.String(30), default='MYTHIC')
    preferred_datetime = db.Column(db.DateTime, nullable=False)
    format = db.Column(db.String(10), default='BO3') # BO1, BO3, BO5
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='OPEN', index=True) # OPEN, MATCHED, COMPLETED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship('Team', back_populates='scrim_requests')
    requested_by = db.relationship('User')
    matches = db.relationship('ScrimMatch', back_populates='request', cascade='all, delete-orphan')


class ScrimMatch(db.Model):
    __tablename__ = 'scrim_matches'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('scrim_requests.id'), nullable=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    match_room_id = db.Column(db.String(50), nullable=True)
    match_room_password = db.Column(db.String(50), nullable=True)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    team1_score = db.Column(db.Integer, default=0)
    team2_score = db.Column(db.Integer, default=0)
    winner_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    status = db.Column(db.String(20), default='SCHEDULED', index=True) # SCHEDULED, COMPLETED, CANCELLED
    screenshot_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    request = db.relationship('ScrimRequest', back_populates='matches')
    team1 = db.relationship('Team', foreign_keys=[team1_id])
    team2 = db.relationship('Team', foreign_keys=[team2_id])
    winner = db.relationship('Team', foreign_keys=[winner_id])


class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    game_title = db.Column(db.String(100), default='Mobile Legends: Bang Bang')
    rules = db.Column(db.Text, nullable=True)
    format = db.Column(db.String(30), default='SINGLE_ELIMINATION')
    max_teams = db.Column(db.Integer, default=16)
    rank_tier_req = db.Column(db.String(30), default='EPIC')
    registration_open = db.Column(db.DateTime, nullable=False)
    registration_close = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='REGISTRATION_OPEN', index=True) # DRAFT, REGISTRATION_OPEN, ONGOING, COMPLETED
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', back_populates='created_tournaments')
    registrations = db.relationship('TournamentRegistration', back_populates='tournament', cascade='all, delete-orphan')
    matches = db.relationship('TournamentMatch', back_populates='tournament', cascade='all, delete-orphan')

    @property
    def approved_registrations(self):
        return [r for r in self.registrations if r.status == 'APPROVED']


class TournamentRegistration(db.Model):
    __tablename__ = 'tournament_registrations'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    seed = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='APPROVED') # PENDING, APPROVED, REJECTED
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    tournament = db.relationship('Tournament', back_populates='registrations')
    team = db.relationship('Team', back_populates='tournament_registrations')


class TournamentMatch(db.Model):
    __tablename__ = 'tournament_matches'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False)
    round = db.Column(db.Integer, nullable=False) # 1 = Quarters/Round 1, 2 = Semis, 3 = Finals
    match_number = db.Column(db.Integer, nullable=False)
    team1_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    team2_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True)
    team1_score = db.Column(db.Integer, default=0)
    team2_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='PENDING') # PENDING, ONGOING, COMPLETED
    scheduled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tournament = db.relationship('Tournament', back_populates='matches')
    team1 = db.relationship('Team', foreign_keys=[team1_id])
    team2 = db.relationship('Team', foreign_keys=[team2_id])
    winner = db.relationship('Team', foreign_keys=[winner_id])


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(200), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    previous_hash = db.Column(db.String(64), nullable=False)
    hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    actor = db.relationship('User')
