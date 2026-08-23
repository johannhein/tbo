# 🏐 TBO 2026 - Turnierauswertung

Eine interaktive, leichtgewichtige Web-Applikation zur Auswertung und Verwaltung des Beachvolleyball-Turniers "Bündener Cup 2026 Mixed" (BVC Calanda). Die Applikation ist mit Python und Streamlit geschrieben und erfordert keine komplexe Datenbank. Alle Daten werden lokal gespeichert.

## ✨ Features

- **Gruppenphase (Vorrunde)**: Verwaltung von 2 Gruppen (A und B) mit jeweils 6 Teams.
- **Automatische Rangliste**: Exakte Rangberechnung nach offiziellen Volleyball-Regeln:
  1. Gewonnene Sätze (Punkte)
  2. Direkter Vergleich (bei Punktegleichstand)
  3. Gesamt-Punktdifferenz (alle erzielten Ballpunkte)
- **K.O.- & Finalrunde (Best-of-3)**: Automatische Zuteilung der Teams in die Zwischenrunde, Halbfinals und Platzierungsspiele anhand der Vorrunden-Ergebnisse. Unterstützung für bis zu 3 Sätze pro Spiel.
- **Gesamtrangliste**: Fair berechneter Endstand (Plätze 1 bis 12) inkl. genauer Auflösung der Ränge 5-8 nach Vorrunden- und Zwischenrunden-Statistik.
- **Druckfertiger Turnierbericht**: Exportiere alle Spiele, Ergebnisse und Endtabellen als sauber formatierte HTML-Seite, die sich perfekt als PDF drucken und archivieren lässt.
- **Datenverwaltung**:
  - Teams & Startgeld-Tracking ("Bezahlt"-Checkboxen).
  - Excel (.xlsx), CSV und JSON Export/Import zur einfachen Datensicherung und Offline-Bearbeitung.
  - Automatisches lokales Backup (`results.json`).

---

## 🛠️ Installation

Die Installation ist in wenigen Schritten erledigt. Du benötigst lediglich **Python 3** auf deinem System.

1. **Repository klonen oder herunterladen:**
   ```bash
   git clone <dein-repo-link>
   cd BeachvolleyTurnier
   ```

2. **Virtuelle Umgebung erstellen (optional, aber empfohlen):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Auf Mac/Linux
   # oder auf Windows:
   # venv\Scripts\activate
   ```

3. **Abhängigkeiten installieren:**
   Installiere alle nötigen Python-Pakete aus der `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Getting Started

Sobald die Installation abgeschlossen ist, kannst du die Applikation lokal starten.

1. **App ausführen:**
   Starte den lokalen Streamlit-Server mit folgendem Befehl im Terminal:
   ```bash
   streamlit run src/main.py
   ```

2. **Im Browser öffnen:**
   Streamlit öffnet nun automatisch deinen Standard-Webbrowser unter `http://localhost:8501`. 

3. **Turnier starten:**
   - Navigiere durch die oberen Tabs (Vorrunde, Felder, Ranglisten).
   - Trage Ergebnisse direkt in die Masken ein und drücke auf "Speichern".
   - Nutze den Reiter "Teams & Daten" um am Ende des Turniers Backups zu erstellen oder den PDF-Report zu generieren.

---


