
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
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download {filename}</a>'

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
        if st.form_submit_button("Login"):
            user = CREDENTIALS.get(username)
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.success("Login successful.")
                st.stop()
            else:
                st.error("Invalid credentials")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.experimental_rerun()

def main_dashboard():
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Go to", ["Dashboard","Table / Records","Import / Export","Analytics","About"])
    df = load_data()

    if page == "Dashboard":
        st.header("Dashboard Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total devices", len(df))
        col2.metric("Faulty", (df['status']=="faulty").sum() if 'status' in df else 0)
        col3.metric("Repaired", (df['status']=="repaired").sum() if 'status' in df else 0)
        st.markdown("---")

        if "status" in df:
            st.subheader("Device Status Summary")
            counts = df['status'].value_counts().reset_index()
            counts.columns = ["status","count"]
            fig = px.pie(counts, names="status", values="count")
            st.plotly_chart(fig, use_container_width=True)

    elif page == "Table / Records":
        st.header("Devices / Repairs Table")
        st.dataframe(df)

    elif page == "Import / Export":
        st.header("Export")
        st.markdown(make_download_link(df), unsafe_allow_html=True)

    elif page == "Analytics":
        st.header("Analytics")
        if "status" in df:
            counts = df['status'].value_counts().reset_index()
            counts.columns = ["status","count"]
            st.table(counts)
            fig = px.bar(counts, x="status", y="count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status column present.")

    elif page == "About":
        st.header("About")
        st.write("Dashboard updated with Plotly support.")

if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
