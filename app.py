import streamlit as st
import pandas as pd
import io
import plotly.express as px
from pathlib import Path
import base64

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
# NOTE: In production, use proper auth. These are example credentials.
CREDENTIALS = {
    "admin": {"password":"admin123","role":"admin"},
    "viewer": {"password":"viewer123","role":"viewer"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

def login():
    st.title("Task & Cameras Repair Dashboard")
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
                st.experimental_rerun()
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
    st.set_page_config(page_title="Repairs Dashboard", layout="wide")
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Go to", ["Dashboard","Table / Records","Import / Export","Analytics","About"])

    df = load_data()

    # Filters
    if page == "Dashboard":
        st.header("Overview")
        st.metric("Total devices", len(df))
        st.metric("Faulty", (df['status']=='faulty').sum() if 'status' in df.columns else 0)
        st.metric("Repaired", (df['status']=='repaired').sum() if 'status' in df.columns else 0)
        st.markdown("---")
        st.subheader("Device Status Summary")
        if 'status' in df.columns and not df['status'].isnull().all():
            counts = df['status'].value_counts().reset_index()
            counts.columns = ["status","count"]
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(counts)
            with col2:
                fig = px.pie(counts, names='status', values='count', title='Devices by status')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available.")

    elif page == "Table / Records":
        st.header("Devices / Repairs Table")
        st.write("Use the filters and search to find records.")
        cols = df.columns.tolist()
        with st.expander("Filters"):
            q_status = st.selectbox("Status", options=['All'] + sorted(df['status'].dropna().unique().tolist()) if 'status' in df.columns else ['All'])
            q_location = st.text_input("Filter by location")
            q_search = st.text_input("Search device name or notes")

        filtered = df.copy()
        if q_status and q_status != 'All':
            filtered = filtered[filtered['status']==q_status]
        if q_location:
            filtered = filtered[filtered['location'].str.contains(q_location, na=False, case=False)]
        if q_search:
            filtered = filtered[filtered['device_name'].str.contains(q_search, na=False, case=False) | filtered['notes'].str.contains(q_search, na=False, case=False)]

        st.dataframe(filtered)

        if st.session_state.role == 'admin':
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
                    save_data(df2)
                    st.success("Record added")
                    st.experimental_rerun()

            st.markdown("### Edit / Delete")
            with st.form("edit_form"):
                edit_id = st.selectbox("Select record ID to edit", options=[''] + df['id'].fillna('').tolist())
                if edit_id:
                    row = df[df['id']==edit_id].iloc[0].to_dict()
                    e_name = st.text_input("Device name", value=row.get("device_name",""))
                    e_type = st.text_input("Device type", value=row.get("device_type",""))
                    e_loc = st.text_input("Location", value=row.get("location",""))
                    e_status = st.selectbox("Status", ["faulty","repaired","awaiting PO","inspected","unknown"], index=0)
                    e_notes = st.text_area("Notes", value=row.get("notes",""))
                    submitted_edit = st.form_submit_button("Save changes")
                    if submitted_edit:
                        df.loc[df['id']==edit_id, 'device_name'] = e_name
                        df.loc[df['id']==edit_id, 'device_type'] = e_type
                        df.loc[df['id']==edit_id, 'location'] = e_loc
                        df.loc[df['id']==edit_id, 'status'] = e_status
                        df.loc[df['id']==edit_id, 'notes'] = e_notes
                        save_data(df)
                        st.success("Saved")
                        st.experimental_rerun()
                if st.form_submit_button("Delete selected"):
                    if edit_id:
                        df = df[df['id']!=edit_id]
                        save_data(df)
                        st.success("Deleted")
                        st.experimental_rerun()

    elif page == "Import / Export":
        st.header("Import & Export")
        st.subheader("Export current data")
        st.markdown(make_download_link(df,"devices_export.csv"), unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("Import CSV / Excel")
        uploaded = st.file_uploader("Upload CSV or Excel", type=['csv','xlsx'])
        if uploaded:
            try:
                if uploaded.name.endswith('.csv'):
                    newdf = pd.read_csv(uploaded, dtype=str)
                else:
                    newdf = pd.read_excel(uploaded, dtype=str)
                save_data(newdf)
                st.success("Imported successfully")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to import: {e}")

    elif page == "Analytics":
        st.header("Analytics")
        if 'status' in df.columns:
            counts = df['status'].value_counts().reset_index()
            counts.columns = ['status','count']
            st.subheader("Counts by status")
            st.table(counts)
            st.subheader("Bar chart")
            fig = px.bar(counts, x='status', y='count', title="Devices by Status")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status column present.")

    elif page == "About":
        st.header("About this dashboard")
        st.write("Modern Streamlit layout with cards & tables. Theme colors: soft blue / gray.")
        st.write("Customize `assets/logo.png` and default credentials in `app.py` before production use.")

# -----------------------
# Entry
# -----------------------
if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
