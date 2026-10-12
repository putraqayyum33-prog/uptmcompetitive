from flask import Blueprint, render_template
from app.models import Team, User

leaderboard_bp = Blueprint('leaderboard', __name__)

RANK_WEIGHTS = {
    'MYTHICAL_IMMORTAL': 10,
    'MYTHICAL_GLORY': 9,
    'MYTHICAL_HONOR': 8,
    'MYTHIC': 7,
    'LEGEND': 6,
    'EPIC': 5,
    'GRANDMASTER': 4,
    'MASTER': 3,
    'ELITE': 2,
    'WARRIOR': 1
}

@leaderboard_bp.route('/')
def index():
    # Fetch all active teams and sort by wins then win rate
    teams = Team.query.filter_by(status='ACTIVE').all()
    sorted_teams = sorted(
        teams,
        key=lambda t: (t.scrim_wins, t.win_rate, t.total_scrims_played),
        reverse=True
    )

    # Fetch top players ranked by MLBB tier
    players = User.query.filter_by(status='ACTIVE').all()
    sorted_players = sorted(
        players,
        key=lambda p: (RANK_WEIGHTS.get(p.rank_tier, 0), p.created_at),
        reverse=True
    )

    return render_template(
        'leaderboard.html',
        teams=sorted_teams,
        players=sorted_players[:20]
    )
