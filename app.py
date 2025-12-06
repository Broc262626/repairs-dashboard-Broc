import streamlit as st
import pandas as pd
import io
import plotly.express as px
from pathlib import Path
import base64
from datetime import datetime

st.set_page_config(page_title="Cameras & Tasks Repair Dashboard", page_icon="assets/logo.png", layout="wide")

DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)
CSV_FILE = DATA_PATH / "devices.csv"

# Utilities
def load_data():
    if CSV_FILE.exists():
        try:
            return pd.read_csv(CSV_FILE, dtype=str)
        except Exception:
            return pd.read_csv(CSV_FILE, dtype=str, encoding='latin1')
    else:
        df = pd.DataFrame(columns=["id","device_name","device_type","location","status","last_inspection","notes","assigned_to","created_at"])
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

# Simple auth (example)
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
    st.image("assets/logo.png", width=140)
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
                st.success("Login successful — loading dashboard...")
                # stop to allow rerun without experimental_rerun issues
                st.stop()
            else:
                st.error("Invalid credentials")


def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.experimental_rerun()


# App sections
def main_dashboard():
    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as **{st.session_state.username}** ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Go to", ["Dashboard","Table / Records","Import / Export","Analytics","About"])
    df = load_data()

    if page == "Dashboard":
        st.header("Overview")
        c1,c2,c3 = st.columns(3)
        c1.metric("Total devices", len(df))
        c1.metric("Faulty", int((df['status']=='faulty').sum()) if 'status' in df.columns else 0)
        c2.metric("Repaired", int((df['status']=='repaired').sum()) if 'status' in df.columns else 0)
        c2.metric("Awaiting PO", int((df['status']=='awaiting PO').sum()) if 'status' in df.columns else 0)
        st.markdown("---")
        st.subheader("Device Status Summary")
        if 'status' in df.columns and not df['status'].isnull().all():
            counts = df['status'].value_counts().reset_index()
            counts.columns = ["status","count"]
            col1,col2 = st.columns([1,1])
            with col1:
                st.dataframe(counts)
            with col2:
                fig = px.pie(counts, names='status', values='count', title='Devices by status')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data available.")

    elif page == "Table / Records":
        st.header("Devices / Repairs Table")
        st.write("Use filters to refine the view.")
        with st.expander("Filters & Search", expanded=True):
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

        st.dataframe(filtered, use_container_width=True)

        if st.session_state.role == 'admin':
            st.markdown("---")
            st.subheader("Add new record")
            with st.form("add_record", clear_on_submit=True):
                new_id = st.text_input("ID")
                new_name = st.text_input("Device name")
                new_type = st.text_input("Device type")
                new_loc = st.text_input("Location")
                new_status = st.selectbox("Status", ["faulty","repaired","awaiting PO","inspected","unknown"])
                new_last = st.date_input("Last inspection")
                new_notes = st.text_area("Notes")
                new_assigned = st.text_input("Assigned to")
                new_created = st.text_input("Created at", value=str(datetime.now().date()))
                if st.form_submit_button("Add record"):
                    new_row = {
                        "id": new_id,
                        "device_name": new_name,
                        "device_type": new_type,
                        "location": new_loc,
                        "status": new_status,
                        "last_inspection": str(new_last),
                        "notes": new_notes,
                        "assigned_to": new_assigned,
                        "created_at": new_created
                    }
                    df2 = df.append(new_row, ignore_index=True)
                    save_data(df2)
                    st.success("Record added")
                    st.experimental_rerun()

            st.markdown("---")
            st.subheader("Edit / Delete record")
            with st.form("edit_form"):
                options = [''] + df['id'].fillna('').tolist() if 'id' in df.columns else ['']
                edit_id = st.selectbox("Select record ID to edit", options=options)
                if edit_id:
                    row = df[df['id']==edit_id].iloc[0].to_dict()
                    e_name = st.text_input("Device name", value=row.get("device_name",""))
                    e_type = st.text_input("Device type", value=row.get("device_type",""))
                    e_loc = st.text_input("Location", value=row.get("location",""))
                    e_status = st.selectbox("Status", ["faulty","repaired","awaiting PO","inspected","unknown"], index=0)
                    e_notes = st.text_area("Notes", value=row.get("notes",""))
                    if st.form_submit_button("Save changes"):
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
        st.markdown(make_download_link(df, "devices_export.csv"), unsafe_allow_html=True)
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

if not st.session_state.logged_in:
    login()
else:
    main_dashboard()
