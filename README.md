# Task & Cameras Repair Dashboard (Streamlit)

**Purpose:** log tasks and camera/device repairs, replacements and inspections. View status in tables and charts.

## Features
- Add / Edit / Delete vehicle/device records (admin only)
- Import / Export CSV / Excel
- Filter, sort and search records
- Admin login vs View-only login
- Status tracking (faulty, repaired, awaiting PO, etc.)
- Basic analytics: counts of devices per status (pie/bar)

## Quick start (local)
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run:
   ```
   streamlit run app.py
   ```
3. Default logins:
   - **Admin:** username `admin`, password `admin123` (change this in `app.py`)
   - **Viewer:** username `viewer`, password `viewer123`

## Deploy to Streamlit Cloud / GitHub
1. Push this repository to GitHub.
2. Create an app on Streamlit Cloud and connect to the repo.
3. Ensure `requirements.txt` is present (it is).
4. Set any secrets (optional) in Streamlit Cloud's secrets manager.

## Repo structure
- `app.py` - main Streamlit app
- `data/devices.csv` - sample data
- `assets/logo.png` - placeholder logo
- `.streamlit/config.toml` - theme (soft blue / gray)
- `requirements.txt` - python deps

----
Customize logos and admin password before production use.
