from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db

profile_bp = Blueprint('profile', __name__)

RANK_TIERS = [
    ('WARRIOR', 'Warrior'),
    ('ELITE', 'Elite'),
    ('MASTER', 'Master'),
    ('GRANDMASTER', 'Grandmaster'),
    ('EPIC', 'Epic'),
    ('LEGEND', 'Legend'),
    ('MYTHIC', 'Mythic'),
    ('MYTHICAL_HONOR', 'Mythical Honor'),
    ('MYTHICAL_GLORY', 'Mythical Glory'),
    ('MYTHICAL_IMMORTAL', 'Mythical Immortal'),
]

@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        mlbb_ign = request.form.get('mlbb_ign', '').strip()
        mlbb_id = request.form.get('mlbb_id', '').strip()
        rank_tier = request.form.get('rank_tier', 'EPIC')
        student_id = request.form.get('student_id', '').strip()
        phone = request.form.get('phone', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip()

        if not display_name:
            flash('Display name cannot be empty.', 'danger')
            return render_template('profile.html', rank_tiers=RANK_TIERS)

        current_user.display_name = display_name
        current_user.mlbb_ign = mlbb_ign
        current_user.mlbb_id = mlbb_id
        current_user.rank_tier = rank_tier
        if student_id:
            current_user.student_id = student_id
        if phone:
            current_user.phone = phone
        if avatar_url:
            current_user.avatar_url = avatar_url

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))

    return render_template('profile.html', rank_tiers=RANK_TIERS)
