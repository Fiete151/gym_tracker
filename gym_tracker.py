import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import pandas as pd
import altair as alt


# --- Konfig ---
USE_OFFLINE = F # 👈 Umschalten zwischen lokal/online

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

    # Vorhandene Übungen aus Google Sheets für Autocomplete
    all_exercises = [row['exercise'] for row in trainings_sh.get_all_records()]
    unique_exercises = sorted(list(set(all_exercises)))

    with st.form("exercise_form"):
        # Übungsauswahl (Vorschläge + Möglichkeit neue einzugeben)
        exercise = st.selectbox(
            "Übung (bereits vorhandene Übungen werden vorgeschlagen)",
            options=unique_exercises + ["Neue Übung..."]
        )
        if exercise == "Neue Übung...":
            exercise = st.text_input("Neue Übung eingeben")

        # Gewicht & Wiederholungen als numerische Eingaben
        weight = st.number_input("Gewicht (kg)", min_value=0.0, step=0.5)
        reps = st.number_input("Wiederholungen", min_value=1, step=1)

        # Satz als Dropdown 1-4
        set_num = st.selectbox("Satz", options=[1, 2, 3, 4])

        submitted = st.form_submit_button("Hinzufügen")

    if submitted:
        if not exercise:
            st.error("Bitte die Übung angeben.")
        else:
            today = date.today().isoformat()
            trainings_sh.append_row([st.session_state["username"], today, exercise, weight, int(reps), set_num])
            st.success(f"Übung '{exercise}' erfolgreich hinzugefügt!")

    if st.button("Abmelden"):
        st.session_state["phase"] = 0
        st.session_state["username"] = None
        st.rerun()

    # --- Trainingsdaten aus Google Sheets ---
    all_data = trainings_sh.get_all_records()
    df = pd.DataFrame(all_data)

    # Spalten bereinigen
    df.columns = [c.strip().lower() for c in df.columns]

    # Nur aktuelle User-Daten
    user_df = df[df["user"] == st.session_state["username"]]

    st.subheader("Meine Trainingsdaten")

    # --- Dropdown zum Filtern nach Übung ---
    exercises = user_df["exercise"].unique().tolist()
    selected_exercise = st.selectbox("Welche Übung anzeigen?", ["Alle"] + exercises)

    # Tabelle filtern für Linien-Diagramm
    if selected_exercise != "Alle":
        filtered_df = user_df[user_df["exercise"] == selected_exercise]
    else:
        filtered_df = user_df

    # --- Zeitraum-Auswahl ---
    filtered_df["date"] = pd.to_datetime(filtered_df["date"], errors='coerce')
    min_date = filtered_df["date"].min()
    max_date = filtered_df["date"].max()

    date_range = st.date_input(
        "Zeitraum wählen",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filter nach Zeitraum
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df["date"] >= pd.to_datetime(start_date)) &
                                  (filtered_df["date"] <= pd.to_datetime(end_date))]


    # Für die Tabelle nur das Datum als String (keine Uhrzeit)
    display_df = filtered_df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

    # Tabelle anzeigen
    st.table(display_df)


    # --- Linien-Diagramm (nur für eine Übung) ---
    if selected_exercise != "Alle" and not filtered_df.empty:
        filtered_df["weight"] = filtered_df["weight"].astype(float)
        filtered_df["reps"] = filtered_df["reps"].astype(int)
        filtered_df["set"] = filtered_df["set"].astype(str)

        line_chart = alt.Chart(filtered_df).mark_line(point=True).encode(
            x='date:T',
            y='reps:Q',
            color=alt.Color('weight:Q', scale=alt.Scale(scheme='viridis'), title='Gewicht (kg)'),
            detail='set:N',
            tooltip=['date:T', 'exercise:N', 'weight:Q', 'reps:Q', 'set:N']
        ).properties(
            title=f"Reps-Verlauf bei {selected_exercise} (Linien nach Satznummer)"
        )

        st.altair_chart(line_chart, use_container_width=True)

    # --- Prozent-Fortschritt-Diagramm ---
    chart = alt.Chart(filtered_df).mark_line(point=True).encode(
        x='date:T',
        y='weight:Q',
        color='exercise:N',
        tooltip=['date:T', 'exercise:N', 'weight:Q', 'weight_pct:Q']
    ).properties(
        title="Prozentualer Gewicht-Fortschritt pro Übung"
    )

    st.altair_chart(chart, use_container_width=True)



    st.subheader("Meine Trainingsdaten bearbeiten")

    # Button, um Bearbeitungsmodus zu aktivieren
    if st.button("Daten bearbeiten"):
        st.session_state["edit_mode"] = True

    if st.session_state.get("edit_mode", False):
        # Sortierbare Tabelle
        sort_col = st.selectbox("Sortiere nach", user_df.columns, index=user_df.columns.get_loc("date"))
        df_sorted = user_df.sort_values(by=sort_col, ignore_index=True)
        st.table(df_sorted)

        # Expander für Bearbeitung
        with st.expander("Zeile bearbeiten"):
            row = st.number_input("Zeile (0-basiert)", 0, len(df_sorted) - 1, 0)

            # Nur bearbeitbare Spalten anzeigen (user nicht)
            editable_cols = [c for c in df_sorted.columns if c != "user"]
            col = st.selectbox("Spalte", editable_cols)
            new_value = st.text_input("Neuer Wert", df_sorted.at[row, col])

            if st.button("Speichern"):
                old_value = df_sorted.at[row, col]
                df_sorted.at[row, col] = new_value  # zeigt sofort die Änderung in Tabelle
                st.success(f"Zeile {row}, Spalte '{col}' von '{old_value}' zu '{new_value}' aktualisiert!")

                # Daten zurück in Google Sheets schreiben
                all_data = trainings_sh.get_all_records()
                all_df = pd.DataFrame(all_data)
                all_df.columns = [c.strip().lower() for c in all_df.columns]

                # Zeile in all_df finden, die geändert werden soll
                user_rows = all_df[all_df["user"] == st.session_state["username"]].reset_index()
                target_index = user_rows.at[row, "index"]

                # Wert aktualisieren
                all_df.at[target_index, col] = new_value

                # Zeile in native Python-Typen konvertieren (JSON-kompatibel)
                row_values = all_df.iloc[target_index].apply(lambda x: x.item() if hasattr(x, "item") else x).tolist()

                # Ganze Zeile zurückschreiben (Google Sheets Zeilen starten bei 1)
                trainings_sh.update(f"A{target_index + 2}:F{target_index + 2}", [row_values])

                # Bearbeitungsmodus ausschalten
                st.session_state["edit_mode"] = False
                st.info("Änderung gespeichert! Die Tabelle wird automatisch aktualisiert.")
                st.rerun()
