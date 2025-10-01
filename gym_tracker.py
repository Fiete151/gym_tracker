import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import pandas as pd



# --- Konfig ---
USE_OFFLINE = True  # 👈 Umschalten zwischen lokal/online

# --- Credentials laden ---
if USE_OFFLINE:
    with open("service_account.json") as f:  # deine lokale Service Account Datei
        creds_data = json.load(f)
else:
    creds_data = json.loads(st.secrets["GOOGLE_CREDS"])

# --- Google Sheets Zugang einrichten (gecached, damit nicht jedes Mal neu) ---
@st.cache_resource
def get_sheet(sheet_name):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_data, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open("gym_tracker_data").worksheet(sheet_name)

users_sh = get_sheet("users")

trainings_sh = get_sheet("trainings")

# --- App State ---
if "phase" not in st.session_state:
    st.session_state["phase"] = 0
if "username" not in st.session_state:
    st.session_state["username"] = None

st.title("Mini Gym Tracker 💪")

# --- Phase 0: Login / Registrierung ---
if st.session_state["phase"] == 0:
    st.subheader("Anmelden/Registrieren")


    with st.form("login_form"):
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        col1, col2 = st.columns(2)
        with col1:
            login_btn = st.form_submit_button("Anmelden")
        with col2:
            register_btn = st.form_submit_button("Registrieren")

    if login_btn:
        users = users_sh.col_values(1)  # Annahme: Benutzernamen in Spalte 1
        passwords = users_sh.col_values(2)  # Passwörter in Spalte 2
        if username in users:
            index = users.index(username)
            if password == passwords[index]:
                st.session_state["username"] = username
                st.session_state["phase"] = 1
                st.rerun()  # direkt umschalten
            else:
                st.error("Falsches Passwort")
        else:
            st.error("Benutzername existiert nicht. Bitte registriere dich zuerst.")

    elif register_btn:
        users = users_sh.col_values(1)
        if username in users:
            st.error("Benutzername bereits vergeben")
        else:
            users_sh.append_row([username, password])
            st.success("Registrierung erfolgreich! Du kannst dich jetzt anmelden.")

# --- Phase 1: Training ---
elif st.session_state["phase"] == 1:
    st.subheader(f"Übung hinzufügen (eingeloggt als {st.session_state['username']})")

    with st.form("exercise_form"):
        exercise = st.text_input("Übung")
        weight = st.text_input("Gewicht (kg)")
        reps = st.text_input("Wiederholungen")
        set_num = st.text_input("Satz")

        submitted = st.form_submit_button("Hinzufügen")

    if submitted:
        if not exercise or not weight or not reps or not set_num:
            st.error("Bitte alle Felder ausfüllen.")
        else:
            try:
                weight_val = float(weight)
                reps_val = int(reps)
                set_val = int(set_num)
                today = date.today().isoformat()

                trainings_sh.append_row([st.session_state["username"], today, exercise, weight_val, reps_val, set_val])
                st.success(f"Übung '{exercise}' erfolgreich hinzugefügt!")
            except ValueError:
                st.error("Gewicht muss eine Zahl, Wiederholungen und Satz ganze Zahlen sein.")

    if st.button("Abmelden"):
        st.session_state["phase"] = 0
        st.session_state["username"] = None
        st.rerun()

    all_data = trainings_sh.get_all_records()  # Liste von Dictionaries
    df = pd.DataFrame(all_data)  # in DataFrame umwandeln

    # --- Nur aktuelle User-Daten ---
    user_df = df[df["user"] == st.session_state["username"]]

    # --- Tabelle anzeigen ---
    st.subheader("Meine Trainingsdaten")
    st.dataframe(user_df)

