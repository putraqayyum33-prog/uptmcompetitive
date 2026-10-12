import os
from datetime import datetime, timedelta
from app import create_app
from app.models import (
    db, User, Team, TeamMember, ScrimRequest, ScrimMatch, 
    Tournament, TournamentRegistration, TournamentMatch, AuditLog
)
from config import Config
from app.utils.security import compute_audit_hash

app = create_app()

def seed_database():
    with app.app_context():
        print("Cleaning and preparing database tables...")
        db.create_all()

        # Clear existing records for a fresh seed
        AuditLog.query.delete()
        TournamentMatch.query.delete()
        TournamentRegistration.query.delete()
        Tournament.query.delete()
        ScrimMatch.query.delete()
        ScrimRequest.query.delete()
        TeamMember.query.delete()
        Team.query.delete()
        User.query.delete()
        db.session.commit()

        print("Seeding users...")
        # 1. Admin
        admin = User(
            email=Config.ADMIN_EMAIL.lower(),
            display_name="System Administrator",
            role="ADMIN",
            status="ACTIVE",
            mlbb_ign="UPTM_Admin",
            mlbb_id="100000001",
            rank_tier="MYTHICAL_IMMORTAL",
            avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=admin"
        )
        admin.set_password(Config.ADMIN_PASSWORD)
        admin.student_id = "UPTM-STAFF-001"
        admin.phone = "+60123456789"
        db.session.add(admin)

        # 2. Captain 1
        captain1 = User(
            email="captain1@student.uptm.edu.my",
            display_name="Ahmad Faiz (Captain)",
            role="CAPTAIN",
            status="ACTIVE",
            mlbb_ign="Faiz_Carry",
            mlbb_id="123456789",
            rank_tier="MYTHICAL_GLORY",
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=faiz"
        )
        captain1.set_password("Student@123")
        captain1.student_id = "SW01081234"
        captain1.phone = "+60112345678"
        db.session.add(captain1)

        # 3. Captain 2
        captain2 = User(
            email="captain2@student.uptm.edu.my",
            display_name="Nur Danial (Captain)",
            role="CAPTAIN",
            status="ACTIVE",
            mlbb_ign="Danial_Mage",
            mlbb_id="987654321",
            rank_tier="MYTHICAL_HONOR",
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=danial"
        )
        captain2.set_password("Student@123")
        captain2.student_id = "SW01085678"
        captain2.phone = "+60198765432"
        db.session.add(captain2)

        # 4. Student Players (8 players)
        players = []
        player_names = ["Haziq", "Irfan", "Aiman", "Syahmi", "Luqman", "Hakim", "Haris", "Zul"]
        ranks = ["MYTHIC", "LEGEND", "MYTHIC", "EPIC", "MYTHICAL_HONOR", "LEGEND", "EPIC", "MYTHIC"]

        for i, name in enumerate(player_names):
            p = User(
                email=f"player{i + 1}@student.uptm.edu.my",
                display_name=f"{name} UPTM",
                role="PLAYER",
                status="ACTIVE",
                mlbb_ign=f"{name}_MLBB",
                mlbb_id=f"20000000{i + 1}",
                rank_tier=ranks[i],
                avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed=player{i + 1}"
            )
            p.set_password("Student@123")
            p.student_id = f"SW0108{2000 + i}"
            p.phone = f"+6013456{1000 + i}"
            db.session.add(p)
            players.append(p)

        db.session.commit()
        print("[OK] Users seeded successfully.")

        # 5. Teams
        print("Seeding teams & rosters...")
        team1 = Team(
            name="UPTM Titans",
            tag="UTT",
            description="The official premier MLBB varsity squad of Universiti Poly-Tech Malaysia.",
            logo_url="https://api.dicebear.com/7.x/identicon/svg?seed=titans",
            captain_id=captain1.id,
            status="ACTIVE"
        )
        db.session.add(team1)

        team2 = Team(
            name="Cyber Knights",
            tag="CKN",
            description="Computing & Engineering faculty esports division.",
            logo_url="https://api.dicebear.com/7.x/identicon/svg?seed=knights",
            captain_id=captain2.id,
            status="ACTIVE"
        )
        db.session.add(team2)
        db.session.commit()

        # Add Captain 1 and players 0..3 to Team 1
        db.session.add(TeamMember(team_id=team1.id, user_id=captain1.id, role="CAPTAIN", status="ACTIVE"))
        for p in players[:4]:
            db.session.add(TeamMember(team_id=team1.id, user_id=p.id, role="STARTER", status="ACTIVE"))

        # Add Captain 2 and players 4..7 to Team 2
        db.session.add(TeamMember(team_id=team2.id, user_id=captain2.id, role="CAPTAIN", status="ACTIVE"))
        for p in players[4:8]:
            db.session.add(TeamMember(team_id=team2.id, user_id=p.id, role="STARTER", status="ACTIVE"))

        db.session.commit()
        print("[OK] Teams & Rosters seeded.")

        # 6. Scrims
        print("Seeding scrim requests & matches...")
        # Open challenge by Team 1
        scrim_open = ScrimRequest(
            team_id=team1.id,
            requested_by_id=captain1.id,
            game_title="Mobile Legends: Bang Bang",
            rank_tier_min="EPIC",
            rank_tier_max="MYTHIC",
            preferred_datetime=datetime.utcnow() + timedelta(days=2, hours=4),
            format="BO3",
            notes="Looking for a friendly competitive BO3 match to test new draft lineup!",
            status="OPEN"
        )
        db.session.add(scrim_open)

        # Scheduled Match between Team 1 and Team 2
        scrim_matched_req = ScrimRequest(
            team_id=team1.id,
            requested_by_id=captain1.id,
            game_title="Mobile Legends: Bang Bang",
            rank_tier_min="LEGEND",
            rank_tier_max="MYTHICAL_GLORY",
            preferred_datetime=datetime.utcnow() + timedelta(days=1),
            format="BO3",
            notes="Faculty scrimmage session.",
            status="MATCHED"
        )
        db.session.add(scrim_matched_req)
        db.session.flush()

        scrim_match = ScrimMatch(
            request_id=scrim_matched_req.id,
            team1_id=team1.id,
            team2_id=team2.id,
            match_room_id="UPTM-88219",
            match_room_password="MLBB99",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            status="SCHEDULED"
        )
        db.session.add(scrim_match)

        # A completed past scrim
        past_match = ScrimMatch(
            team1_id=team1.id,
            team2_id=team2.id,
            match_room_id="UPTM-10492",
            match_room_password="WAR772",
            scheduled_at=datetime.utcnow() - timedelta(days=3),
            team1_score=2,
            team2_score=1,
            winner_id=team1.id,
            status="COMPLETED"
        )
        db.session.add(past_match)
        db.session.commit()
        print("[OK] Scrim lobby seeded.")

        # 7. Tournament & Bracket
        print("Seeding tournament & bracket tree...")
        tournament = Tournament(
            title="UPTM MLBB Inter-Faculty Championship 2026",
            description="The official premier campus tournament organized by UPTM E-Sports Club. Faculty pride, cash prizes, and varsity roster selection.",
            game_title="Mobile Legends: Bang Bang",
            rules="1. Standard MLBB 5v5 Tournament Draft Pick mode.\n2. All players must be registered UPTM students.\n3. Matches are BO3, Grand Finals BO5.\n4. Screenshot submission required after match completion.",
            format="SINGLE_ELIMINATION",
            max_teams=16,
            rank_tier_req="EPIC",
            registration_open=datetime.utcnow() - timedelta(days=5),
            registration_close=datetime.utcnow() + timedelta(days=10),
            status="REGISTRATION_OPEN",
            created_by_id=admin.id
        )
        db.session.add(tournament)
        db.session.flush()

        # Register both teams
        reg1 = TournamentRegistration(tournament_id=tournament.id, team_id=team1.id, seed=1, status="APPROVED")
        reg2 = TournamentRegistration(tournament_id=tournament.id, team_id=team2.id, seed=2, status="APPROVED")
        db.session.add_all([reg1, reg2])

        # Seed initial bracket structure (Quarterfinals, Semifinals, Finals)
        # Round 1 (Quarterfinals)
        m1 = TournamentMatch(tournament_id=tournament.id, round=1, match_number=1, team1_id=team1.id, team2_id=team2.id, team1_score=2, team2_score=0, winner_id=team1.id, status="COMPLETED")
        m2 = TournamentMatch(tournament_id=tournament.id, round=1, match_number=2, team1_id=None, team2_id=None, team1_score=0, team2_score=0, status="PENDING")
        # Round 2 (Semifinals)
        m3 = TournamentMatch(tournament_id=tournament.id, round=2, match_number=1, team1_id=team1.id, team2_id=None, team1_score=0, team2_score=0, status="PENDING")
        # Round 3 (Grand Finals)
        m4 = TournamentMatch(tournament_id=tournament.id, round=3, match_number=1, team1_id=None, team2_id=None, team1_score=0, team2_score=0, status="PENDING")
        db.session.add_all([m1, m2, m3, m4])

        # 8. Initial Audit Log
        prev_hash = "GENESIS_HASH_UPTM_ESPORTS_2026"
        now_str = datetime.utcnow().isoformat()
        first_hash = compute_audit_hash(str(admin.id), "SYSTEM_INIT", "Database", "0", prev_hash, now_str)
        audit_log = AuditLog(
            actor_id=admin.id,
            action="SYSTEM_INIT",
            target_type="Database",
            target_id="0",
            details="Initial platform database seeding and genesis configuration",
            ip_address="127.0.0.1",
            previous_hash=prev_hash,
            hash=first_hash,
            created_at=datetime.utcnow()
        )
        db.session.add(audit_log)

        db.session.commit()
        print("[OK] Tournament & Audit log seeded.")
        print("\n=======================================================")
        print("  UPTM ESPORTS PLATFORM SEED COMPLETED SUCCESSFULLY!  ")
        print("=======================================================")
        print("Admin Login:   admin@uptm.edu.my  / Admin@UPTM2026!")
        print("Captain Login: captain1@student.uptm.edu.my / Student@123")
        print("Player Login:  player1@student.uptm.edu.my / Student@123")
        print("Or use 1-click 'Demo Login' buttons on the website!")
        print("=======================================================\n")

if __name__ == "__main__":
    seed_database()
