# 🏐 Travemünder Beach Open – Turnierauswertung

---

## Inhaltsverzeichnis

- [Features](#features)
- [Voraussetzungen](#voraussetzungen)
- [Einrichten der App](#einrichten-der-app)
- [Starten der App](#starten-der-app)
- [Unterstützt von](#unterstützt-von)
- [Inspiration](#inspiration)
- [Lizenz](#lizenz)

---

Eine interaktive, leichtgewichtige Web-Anwendung zur Auswertung und Verwaltung der **Travemünder Beach Open** (TGR Rangenberg).  
Entwickelt mit **Python** und **Streamlit**, erfordert keine externe Datenbank – alle Daten werden lokal gespeichert.  
Das Projekt befindet sich in der Entwicklung und ist noch nicht vollständig abgeschlossen.

---

## Features

### Turnierkonfiguration
- Definieren von Turniertypen (z. B. Damen, Herren, Quattro) mit:
  - Spieltag
  - Netzhöhe
  - Anzahl verfügbarer Felder

### Neues Turnier
- **Anmeldedaten importieren** aus CSV oder XLSX
- Auswahl des Turniertyps
- Bearbeitung der Teilnehmerliste (Hinzufügen, Löschen, Ändern)
- **Automatische Gruppenbildung**:
  - Festlegung der Anzahl der Gruppen
  - Auswahl der Gruppenköpfe
  - Vereinsbasierte Verteilung: Teams aus demselben Verein werden, soweit möglich, in verschiedene Gruppen aufgeteilt
  - Automatische Zuweisung von Feldern zu Gruppen
- Einstellung des Spielmodus für vollständige und unvollständige Gruppen

### Vorrunde
- Nachträgliche Anpassung von Teams
- Berücksichtigung verspäteter Teams (spätere Spielzeiten)
- Generierung von Spielprotokollen im HTML-Format (für Druck oder Weitergabe)

### Automatische Rangliste
Genau nach offiziellen Volleyball-Regeln berechnet:
1. Gewonnene Sätze (Punkte)
2. Direkter Vergleich (bei Punktegleichstand)
3. Punktdifferenz (alle erzielten Ballpunkte)

---

## Voraussetzungen

Dieses Projekt erfordert **Python 3.13** (oder höher), da es moderne Sprachfeatures und Bibliotheken nutzt, die in älteren Versionen nicht verfügbar sind.  
Die folgende Anleitung ist für Windows-Systeme optimiert.

> ✅ Wenn Python bereits installiert ist, kannst du direkt mit [Herunterladen des Repositorys](#herunterladen-des-repositorys) fortfahren.

---

### Installation von Python 3.13

1. Gehe zu: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Direkter Link zu [Python 3.13.15](https://www.python.org/downloads/release/python-31315/)
2. Lade die **Windows-Installer (64-Bit)** herunter (z. B. `python-3.13.15-amd64.exe`)
3. Führe die Installation aus und **aktiviere die Option**:
   ```
   ✅ Add Python to PATH
   ```
4. Öffne ein neues Terminal (PowerShell oder CMD) und prüfe die Installation:
   ```bash
   python --version
   ```
   → Sollte `Python 3.13.15` oder höher anzeigen.

---

### Herunterladen des Repositorys

Es gibt zwei Möglichkeiten, das Projekt lokal zu erhalten: **Git-Klonen** oder **ZIP-Download**.
Für das **Git-Klonen** ist eine weitere Installation notwendig.

---

#### Methode 1: Projekt über Git klonen

1. Installiere **Git** von [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Wähle bei der Installation:
   - ✅ *Use Git and optional Unix tools from the Command Prompt*
3. Öffne ein Terminal und teste die Installation:
   ```bash
   git --version
   ```

> **Tipp:** Öffne den Datei-Explorer, gehe in dein gewünschtes Projektverzeichnis und klicke mit der rechten Maustaste → „In Terminal öffnen“.

Führe die folgenden Befehle aus:

```bash
git clone https://github.com/johannhein/tbo.git
cd tbo
```

[Weiter mit: Einrichten der App](#einrichten-der-app)

---

#### Methode 2: ZIP-Download (ohne Git)

Wenn du Git nicht installieren möchtest:

1. Gehe zu: [https://github.com/johannhein/tbo](https://github.com/johannhein/tbo)
2. Klicke auf den **„Code“-Button** (oben rechts)
3. Wähle **„Download ZIP“** aus
4. Entpacke die ZIP-Datei an einem beliebigen Ort
5. Die Ordnerstruktur sollte nun so aussehen:
   ```
   tbo-main/
   └── tbo-main/
       ├── .streamlit/
       ├── assets/
       ├── data/
       ├── src/
       └── ...
   ```
6. **Lösche den oberen Ordner `tbo-main`** und benenne den darin enthaltenen Ordner in `tbo` um:
   ```
   tbo/
   ├── .streamlit/
   ├── assets/
   ├── data/
   ├── src/
   └── ...
   ```
7. Gehe in den Ordner `tbo` und öffne ein Terminal (rechte Maustaste → „In Terminal öffnen“).

---

## Einrichten der App

1. Erstelle eine virtuelle Umgebung (empfohlen):
   ```bash
   python -m venv .venv
   ```

2. Aktiviere die virtuelle Umgebung:
   ```bash
   .venv\Scripts\activate
   ```

   ⚠️ **Falls ein Fehler erscheint** (z. B. „Execution Policy“), führe Folgendes aus und wiederhole den vorherigen Schritt:

   ```bash
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. Installiere die Abhängigkeiten:
   ```bash
   pip install .
   ```

---

## Starten der App

Nach erfolgreicher Einrichtung kannst du die Anwendung starten:

1. **App ausführen:**
   ```bash
   streamlit run src/main.py
   ```

2. **Im Browser öffnen:**  
   Streamlit öffnet automatisch deinen Standard-Webbrowser unter:
   → `http://localhost:8501`

3. **Turnier starten:**  
   Navigiere über die oberen Tabs:
   - **Voreinstellungen**
   - **Neues Turnier**
   - **Vorrunde**

4. **Beenden der App:**  
   Drücke `STRG + C` im Terminal, um die Anwendung zu stoppen.

---

## Unterstützt von

- [TGR Rangenberg](https://www.tgr-rangenberg.de)

---

## Inspiration

DiGrundgerüst und die idee für die Umsetzung wurde übernommen und speziell für das **Travemünder Beach Open** angepasst und erweitert.

---

## Lizenz

Dieses Projekt ist unter der [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) lizenziert.  
Nutzung und Bearbeitung sind nur für **nicht-kommerzielle Zwecke** erlaubt – mit Namensnennung
