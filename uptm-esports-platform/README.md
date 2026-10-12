# UPTM Secure Competitive Gaming Platform (Flask Edition)

A full-stack, lightweight esports web application developed for the **Universiti Poly-Tech Malaysia (UPTM) E-Sports Club**. Designed specifically for campus Mobile Legends: Bang Bang (MLBB) competitive gaming, scrim matchmaking, tournament bracket management, and verified roster tracking.

---

## Tech Stack

- **Backend**: Python 3.14 + Flask 3.x
- **Database**: SQLite (`instance/uptm_esports.db`) via Flask-SQLAlchemy
- **Frontend**: HTML5 + Jinja2 Templates + Bootstrap 5.3 + Bootstrap Icons
- **Authentication**: Flask-Login + Werkzeug Security (scrypt/pbkdf2 hashing)
- **Security**: AES-256-GCM encryption for PII, SHA-256 append-only audit chaining, CSRF protection, and institutional email domain restriction (`@student.uptm.edu.my`)

---

## Quick Start Guide

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Initialize & Seed Database
This creates the SQLite database and populates it with realistic demo rosters, scrims, tournament brackets, and test accounts:
```bash
python seed.py
```

### 3. Run Application
```bash
python run.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## Ready-to-Use Accounts for Evaluation / Viva

You can either log in using the credentials below, or click any of the **1-Click Demo Login** buttons on the navigation bar / login page:

| Role | Email | Password | Persona |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@uptm.edu.my` | `Admin@UPTM2026!` | UPTM Esports Coordinator |
| **Team Captain** | `captain1@student.uptm.edu.my` | `Student@123` | Ahmad Faiz (UPTM Titans) |
| **Team Captain** | `captain2@student.uptm.edu.my` | `Student@123` | Nur Danial (Cyber Knights) |
| **Student Player** | `player1@student.uptm.edu.my` | `Student@123` | Haziq UPTM (Player) |

---

## Key Features

1. **Scrim Lobby & Matchmaking**:
   - Filter scrim challenges by MLBB rank tier (Epic, Legend, Mythic, Mythical Glory).
   - Post challenges with match formats (BO1, BO3, BO5) and preferred date/time.
   - Accept challenge to automatically generate **Custom Match Room ID & Password**.
   - Submit match results and verify victory records.

2. **Campus Tournaments**:
   - Single elimination visual bracket tree (Quarterfinals, Semifinals, Grand Finals).
   - Captain team registration with capacity limits.
   - Official tournament rules and guidelines.

3. **Team & Roster Management**:
   - Create team rosters with team tag, logo, and bio.
   - Captain controls: Add student players by institutional email or IGN, kick members.
   - Track team win rates and scrim history.

4. **Leaderboards**:
   - 1st, 2nd, and 3rd place podium displays.
   - Team power rankings sorted by wins and win rate.
   - Top player ranking by MLBB tier.

5. **Institutional Security & PDPA Compliance**:
   - Restricted strictly to `@student.uptm.edu.my` and `@uptm.edu.my`.
   - Sensitive PII (Student ID & Phone) encrypted at rest with AES-256-GCM.
   - Tamper-evident SHA-256 audit chaining visible in the Admin Portal.

