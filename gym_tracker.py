import streamlit as st
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


service_account_info = json.loads(st.secrets["GOOGLE_CREDS"])

# 1️⃣ Google Sheets Zugang einrichten
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
gc = gspread.authorize(creds)


# 2️⃣ Sheet öffnen
sh = gc.open("gym_tracker_data").sheet1  # Name deines Sheets


phase = 0

# --- App-Titel ---
st.title("Mini Gym Tracker 💪")

if phase == 0:
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")
    st.subheader("Anmelden/Registrieren")

    if st.button("Anmelden"):
        users = sh.col_values(1)  # Annahme: Benutzernamen in Spalte 1
        passwords = sh.col_values(2)  # Passwörter in Spalte 2
        if username in users:
            index = users.index(username)
            if password == passwords[index]:
                st.success(f"Willkommen zurück, {username}!")
                phase = 1  # Phase wechseln, z.B. Hauptseite anzeigen
            else:
                st.error("Falsches Passwort")
        else:
            st.error("Benutzername existiert nicht. Bitte registriere dich zuerst.")

    elif st.button("Registrieren"):
        users = sh.col_values(1)
        if username in users:
            st.error("Benutzername bereits vergeben")
        else:
            sh.append_row([username, password])
            st.success("Registrierung erfolgreich! Du kannst dich jetzt anmelden.")

elif phase == 1:
    st.subheader("Übung hinzufügen")

    exercise = st.text_input("Übung")
    weight = st.text_input("Gewicht (kg)")
    reps = st.text_input("Wiederholungen")
    set_num = st.text_input("Satz")

    if st.button("Hinzufügen"):
        # Eingaben prüfen
        if not exercise or not weight or not reps or not set_num:
            st.error("Bitte alle Felder ausfüllen.")
        else:
            try:
                # Optional: numerische Felder prüfen
                weight_val = float(weight)
                reps_val = int(reps)
                set_val = int(set_num)

                # In Google Sheet eintragen
                sh.append_row([exercise, weight_val, reps_val, set_val])
                st.success(f"Übung '{exercise}' erfolgreich hinzugefügt!")


            except ValueError:
                st.error("Gewicht muss eine Zahl, Wiederholungen und Satz ganze Zahlen sein.")
