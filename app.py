
import streamlit as st
import pandas as pd
import io
import plotly.express as px
from pathlib import Path
import base64

DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)
CSV_FILE = DATA_PATH / "devices.csv"

def load_data():
    if CSV_FILE.exists():
        return pd.read_csv(CSV_FILE, dtype=str)
    df = pd.DataFrame(columns=["id","device_name","device_type","location","status",
                               "last_inspection","notes","assigned_to","created_at"])
    df.to_csv(CSV_FILE, index=False)
    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

CREDENTIALS = {
    "admin": {"password":"admin123","role":"admin"},
    "viewer": {"password":"viewer123","role":"viewer"}
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("Login")
    st.image("assets/logo.png", width=150)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            user = CREDENTIALS.get(u)
            if user and p == user["password"]:
                st.session_state.logged_in = True
                st.session_state.role = user["role"]
                st.success("Login successful")
                st.stop()
            else:
                st.error("Invalid")

def main():
    st.title("Dashboard Fixed Version")
    df = load_data()
    st.dataframe(df)

if not st.session_state.logged_in:
    login()
else:
    main()
