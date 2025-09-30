import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials

st.title("Google Sheets Connection Test 🚀")

# 🔹 Prüfen, ob Secret geladen werden kann
if "GOOGLE_CREDS" not in st.secrets:
    st.error("❌ Secret 'GOOGLE_CREDS' nicht gefunden! Bitte im Streamlit Cloud Dashboard eintragen.")
else:
    try:
        # Secret auslesen und in JSON umwandeln
        service_account_info = json.loads(st.secrets["GOOGLE_CREDS"])
        st.success("✅ Secret geladen!")
        st.json(service_account_info)  # zeigt die Keys im Dashboard

        # Google Sheets Verbindung aufbauen
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        gc = gspread.authorize(creds)

        # Test: erstes Sheet öffnen
        sh = gc.open("gym_tracker_data").sheet1
        st.success(f"✅ Verbindung zu '{sh.title}' erfolgreich!")

    except json.JSONDecodeError as e:
        st.error(f"❌ JSON Fehler: {e}")
    except Exception as e:
        st.error(f"❌ Google Sheets Fehler: {e}")
