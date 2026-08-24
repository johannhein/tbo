# 🏐 Travemünder Beach Open - Turnierauswertung

Eine interaktive, leichtgewichtige Web-Applikation zur Auswertung und Verwaltung der Travemünder Beach Open (TGR Rangenberg). Die Applikation ist mit Python und Streamlit geschrieben und erfordert keine komplexe Datenbank. Alle Daten werden lokal gespeichert. Sie befindet sich in der Entwicklung und noch unvollständig.

## ✨ Features

- **Voreinstellungen**: Definieren der verschiedenen Turniere mit Spieltag, Netzhöhe und verfügbaren Feldern
- **Neues Turnier**:
  - Einlesen der Anmeldedaten
  - Auswählen des Turniertyps
  - Bearbeiten der Teilnehmerliste
  - Erstellen der Gruppen
    - Auswahl der Anzahl an Gruppen
    - Setzen von Gruppenköpfen
    - Teams aus den gleichen Vereinen werden, wenn möglich in verschiedene Gruppen aufgeteilt
    - automatische Zuweisung der einzelnen Felder zu den Gruppen
  - Einstellen der Spielmodus für vollständige und unvollständige Gruppen
- **Vorrunde**:
  - Tauschen von Teams nochmal möglich
  - Verspätete teams bekommen spätere Spiele
  - generieren von Spielprotokollen
- **Automatische Rangliste**: Exakte Rangberechnung nach offiziellen Volleyball-Regeln:
  1. Gewonnene Sätze (Punkte)
  2. Direkter Vergleich (bei Punktegleichstand)
  3. Gesamt-Punktdifferenz (alle erzielten Ballpunkte)

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
   # Linux/macOS
   source .venv/bin/activate
   # Windows
   .venv\Scripts\activate
   ```

3. **Abhängigkeiten installieren:**
   Installiere alle nötigen Python-Pakete aus der `pyprojeck.toml`:
   ```bash
   pip install .
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
   - Navigiere durch die oberen Tabs (Voreinstellungen, Neues Turnier, Vorrunde).

---


