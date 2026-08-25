# 🏐 Travemünder Beach Open - Turnierauswertung

---

[[_TOC_]]

---

Eine interaktive, leichtgewichtige Web-Applikation zur Auswertung und Verwaltung der **Travemünder Beach Open** (TGR Rangenberg).  
Die App ist mit **Python** und **Streamlit** entwickelt und erfordert keine komplexe Datenbank – alle Daten werden lokal gespeichert.  
Das Projekt befindet sich in der Entwicklung und ist noch unvollständig.

---

## Features

- **Turnierkonfiguration**:  
  Definieren von Turniertypen mit Spieltag, Netzhöhe und verfügbaren Feldern.

- **Neues Turnier**:  
  - Einlesen der Anmeldedaten aus CSV/XLSX  
  - Auswahl des Turniertyps (Damen, Herren, Quattro, etc.)  
  - Bearbeitung der Teilnehmerliste  
  - Erstellen der Gruppen:  
    - Anzahl der Gruppen festlegen  
    - Gruppenköpfe auswählen  
    - Teams aus demselben Verein werden, wenn möglich, in verschiedene Gruppen aufgeteilt  
    - Automatische Zuweisung der Felder zu den Gruppen  
  - Einstellung des Spielmodus für vollständige und unvollständige Gruppen

- **Vorrunde**:  
  - Teams können nachträglich angepasst werden  
  - Verspätete Teams erhalten spätere Spielzeiten  
  - Generieren von Spielprotokollen (HTML)

- **Automatische Rangliste**:  
  Genau nach offiziellen Volleyball-Regeln berechnet:  
  1. Gewonnene Sätze (Punkte)  
  2. Direkter Vergleich (bei Punktegleichstand)  
  3. Punktdifferenz (alle erzielten Ballpunkte)

---

## Setup

Dieses Projekt erfordert **Python 3.13** (oder höher), da es moderne Sprachfeatures und Bibliotheken nutzt, die in älteren Versionen nicht verfügbar sind. Die folgenden ANleitung ist für Windows PCs geschrieben.

Wenn Python bereits installiert ist, kannst du [hier](#herunterladen-des-repositorys) weitermachen.

---

###  **Installation von Python 3.13**

1. Gehe zu: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    - Direkter Link zu [Python 3.13](https://www.python.org/downloads/release/python-31315/)
2. Lade die **Python 3.13.x**-Version herunter (z. B. `Windows installer (64-bit)` – Datei: `python-3.13.15-amd64.exe`)
    - Der **Windows Download Python Installer Manager** ist nicht notwendig.
3. Führe die Installation aus und **markiere die Option**:
   ```
   ✅ Add Python to PATH
   ```
4. Öffne ein neues Terminal (PowerShell oder CMD) und prüfe:
   ```bash
   python --version
   ```

---

## Herunterladen des Repositorys

Es gibt nun 2 Möglichkeiten das Projekt lokal zu speichern. Entweder mn installiert `git` oder lädt die Daten manuell als Zip-Datei von der Github-Seite herunter. 

#### Methode 1 Projekt über Git klonen
Um das Projekt über `git` zu klonen, musst du **Git** installieren:

- Lade Git von [https://git-scm.com/download/win](https://git-scm.com/download/win) herunter.
- Führe die Installation aus und wähle **"Use Git and optional Unix tools from the Command Prompt"**.


> ✅ Nach der Installation kannst du `git --version` in dem Terminal testen.

Terminal-Shell öffnen
Öffne den Datei-Explorer und gehe in ein Verzeichnis, wo du die Projektdaten speichern möchtest.
Klicke mit der rechten Maustaste in dem Ordner auf eine leere Stelle und wähle „In Terminal öffnen“ aus dem Menü.
Führe anschließen die folgenden Befehle in dem Terminal nacheinander aus.

Repository klonen:
```bash
git clone https://github.com/johannhein/tbo.git
cd tbo
```

[Hier gehts dann weiter.](#installation-des-tools)

### Methode 2: ZIP-Download (ohne Git)

Wenn du Git nicht installieren möchtest, kannst du das Projekt einfach als ZIP-Datei herunterladen:

1. Gehe zu: [https://github.com/johannhein/tbo](https://github.com/johannhein/tbo)
2. Klicke auf den **"Code"-Button** (oben rechts).
3. Wähle **"Download ZIP"** aus.
4. Entpacke die ZIP-Datei an einem beliebigen Ort wo das Tool später gespeichert werden soll.
5. Die Struktur sollte nun in deinem Verzeichnis wie folgt aussehen:
    ```
    tbo-main/
    └── tbo-main/
        ├── .streamlit/
        ├── assets/
        ├── data/
        │   ├── ...
        ├── src/
        │   ├── ...
        └── ...
    ```
6. Lösche den obersten Ordner und nenne den anderen Ordner `tbo-main` in `tbo` um. Sodass es nun wie folgt aussieht:
    ```
    tbo/
    ├── .streamlit/
    ├── assets/
    ├── data/
    │   ├── ...
    ├── src/
    │   ├── ...
    └── ...
    ```
7. Gehe in den Ordner `tbo`.
8. Klicke mit der rechten Maustaste in dem Ordner auf eine leere Stelle und wähle „In Terminal öffnen“ aus dem Menü.
Führe anschließen die folgenden Befehle in dem Terminal nacheinander aus.

## Installation des Tools

1. Erstelle eine virtuelle Umgebung (empfohlen):
   ```bash
   python -m venv .venv
   ```

2. Aktiviere die virtuelle Umgebung:
     ```bash
     .venv\Scripts\activate
     ```
   
    ⚠️ Wenn in Windows eine Fehlermeldung kommt: Führe Folgendes aus und wiederhole anschließend den vorherigen Befehl nochmal:

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. Installiere die Abhängigkeiten:
   ```bash
   pip install -e .
   ```

---

## 🚀 Getting Started

Sobald die Installation abgeschlossen ist, kannst du die Applikation starten:

1. **App ausführen:**
   ```bash
   streamlit run src/main.py
   ```

2. **Im Browser öffnen:**  
   Streamlit öffnet automatisch deinen Standard-Webbrowser unter:  
   → `http://localhost:8501`

3. **Turnier starten:**  
   - Navigiere durch die oberen Tabs: **Voreinstellungen**, **Neues Turnier**, **Vorrunde**.

4. **Beenden:**  
   - Drücke `STRG + C` im Terminal, um die App zu stoppen.

---

## Unterstützt von

- [TGR Rangenberg](https://www.tgr-rangenberg.de)

---

## Inspiration & Attribution

Dieses Projekt wurde inspiriert von:
- [**sandly**](https://github.com/o3d1/sandly) – von o3d1

Wir haben die Kernkonzepte übernommen und für das **Travemünder Beach Open** angepasst.

---

## Lizenz

Dieses Projekt ist unter der [MIT-Lizenz](LICENSE) veröffentlicht.