import streamlit as st
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


# 1️⃣ Google Sheets Zugang einrichten
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
gc = gspread.authorize(creds)


# 2️⃣ Sheet öffnen
sh = gc.open("gym_tracker_data").sheet1  # Name deines Sheets


phase = 0

# --- App-Titel ---
st.title("Mini Gym Tracker 💪, Updated, second time")



if phase == 0:
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort")
    st.subheader("Anmelden/Registrieren")
    if st.button("Anmelden"):
        st.subheader("Anmelden/Registrieren")
    elif st.button("Registrieren"):
        users = sh.col_values(1)
        if username in users:
            st.error("Benutzername bereits vergeben")
        else:
            sh.append_row([username, password])
            st.success("Registrierung erfolgreich! Du kannst dich jetzt anmelden.")





