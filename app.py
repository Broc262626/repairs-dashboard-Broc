
import streamlit as st
import pandas as pd
import io
import plotly.express as px
from pathlib import Path
import base64

st.set_page_config(
    page_title="Cameras & Tasks Repair Dashboard",
    page_icon="assets/logo.png",
    layout="wide"
)

DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)
CSV_FILE = DATA_PATH / "devices.csv"

# -----------------------
# Utilities
# -----------------------
def load_data():
    if CSV_FILE.exists():
        return pd.read_csv(CSV_FILE, dtype=str)
    else:
        df = pd.DataFrame(columns=[
            "id","device_name","device_type","location","status",
            "last_inspection","notes","assigned_to","created_at"
        ])
        df.to_csv(CSV_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def make_download_link(df, filename="devices_export.csv"):
    towrite = io.BytesIO()
    df.to_csv(towrite, index=False)
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

# -----------------------
# Simple auth
# -----------------------
CREDENTIALS = {
    "admin": {"password":"admin123","role":"admin"},
    "viewer": {"password":"viewer123","role":"viewer"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

def login():
    st.title("Cameras & Tasks Repair Dashboard")
    st.image("assets/logo.png", width=150)
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            user = CREDENTIALS.get(username)
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.success("Login successful...")
                st.stop()
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.experimental_rerun()

# -----------------------
# App Sections
# -----------------------
def main_dashboard():
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Go to", ["Dashboard","Table / Records","Import / Export","Analytics","About"])
    df = load_data()

    if page == "Dashboard":
        st.header("Dashboard Overview")
        left, mid, right = st.columns(3)
        left.metric("Total devices", len(df))
        left.metric("Faulty", (df['status']=="faulty").sum() if 'status' in df.columns else 0)
        mid.metric("Repaired", (df['status']=="repaired").sum() if 'status' in df.columns else 0)
        mid.metric("Awaiting PO", (df['status']=="awaiting PO").sum() if 'status' in df.columns else 0)
        st.markdown("---")
        st.subheader("Device Status Summary")
        if 'status' in df.columns and not df['status'].isnull().all():
            counts = df['status'].value_counts().reset_index()
            counts.columns = ["status","count"]
            col1, col2 = st.columns(2)
            col1.dataframe(counts)
            fig = px.pie(counts, names='status', values='count', title='Devices by status')
            col2.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available.")

    elif page == "Table / Records":
        st.header("Devices / Repairs Table")
        with st.expander("Filters"):
            q_status = st.selectbox("Status", ['All'] + sorted(df['status'].dropna().unique()) if 'status' in df else ['All'])
            q_location = st.text_input("Filter by location")
            q_search = st.text_input("Search device name or notes")

        filtered = df.copy()
        if q_status != "All":
            filtered = filtered[filtered['status']==q_status]
        if q_location:
            filtered = filtered[filtered['location'].str.contains(q_location, case=False, na=False)]
        if q_search:
            filtered = filtered[
                filtered['device_name'].str.contains(q_search, case=False, na=False)
                | filtered['notes'].str.contains(q_search, case=False, na=False)
            ]

        st.dataframe(filtered)

        if st.session_state.role == "admin":
            st.markdown("### Add new record")
            with st.form("add_record", clear_on_submit=True):
                new = {
                    "id": st.text_input("ID"),
                    "device_name": st.text_input("Device name"),
                    "device_type": st.text_input("Device type"),
                    "location": st.text_input("Location"),
                    "status": st.selectbox("Status", ["faulty","repaired","awaiting PO","inspected","unknown"]),
                    "last_inspection": st.date_input("Last inspection"),
                    "notes": st.text_area("Notes"),
                    "assigned_to": st.text_input("Assigned to"),
                    "created_at": st.text_input("Created at")
                }
                if st.form_submit_button("Add record"):
                    df2 = df.append(new, ignore_index=True)
                    df2.to_csv(CSV_FILE, index=False)
                    st.success("Record added")
                    st.experimental_rerun()

    elif page == "Import / Export":
        st.header("Import & Export")
        st.subheader("Export current data")
        st.markdown(make_download_link(df,"devices_export.csv"), unsafe_allow_html=True)

    elif page == "Analytics":
        st.header("Analytics")
        if "status" in df:
            counts = df['status'].value_counts().reset_index()
            counts.columns = ["status","count"]
            st.table(counts)
            st.plotly_chart(px.bar(counts, x='status', y='count'), use_container_width=True)
        else:
            st.info("No status column present.")

    elif page == "About":
        st.header("About")
        st.write("Dashboard customized successfully.")

if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
