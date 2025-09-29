import streamlit as st
import json
import os



DATA_FILE = "training_data.json"

phase = 0


# --- Funktionen ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return [json.loads(line) for line in f]
    return []

def save_data(entry):
    with open(DATA_FILE, "a") as f:
        json.dump(entry, f)
        f.write("\n")

# --- App-Titel ---
st.title("Mini Gym Tracker 💪")



if phase == 0:
    st.subheader("Anmelden/Account erstellen")



if phase == 1:
    st.subheader("Neue Übung eintragen")
    exercise = st.text_input("Übung")
    weight = st.number_input("Gewicht (kg)", min_value=0, step=1)
    reps = st.number_input("Wiederholungen", min_value=0, step=1)
    sets = st.number_input("Sätze", min_value=0, step=1)

    if st.button("Speichern"):
        if exercise:
            entry = {"exercise": exercise, "weight": weight, "reps": reps, "sets": sets}
            save_data(entry)
            st.success(f"{exercise} gespeichert!")
        else:
            st.error("Bitte Übungsnamen eingeben!")

# --- Fortschritt anzeigen ---
    st.subheader("Fortschritt anzeigen")
    data = load_data()

    if data:
        # Auswahl der Übung
        exercises = list(set([d["exercise"] for d in data]))
        selected = st.selectbox("Übung auswählen", exercises)

        # Daten filtern
        filtered = [d for d in data if d["exercise"] == selected]

        # Tabelle anzeigen
        st.write(f"Alle Einträge für **{selected}**:")
        st.table(filtered)

    else:
        st.info("Noch keine Trainingsdaten vorhanden. Trage zuerst Übungen ein!")
