# 🏐 Travemünder Beach Open – Turnierplaner

---

## Inhaltsverzeichnis

- [1. Features](#1-features)
- [2. Voraussetzungen](#2-voraussetzungen)
- [3. Einrichten der App](#3-einrichten-der-app)
- [4. Starten der App](#4-starten-der-app)
- [5.Unterstützt von](#5-unterstützt-von)
- [6.Inspiration](#6-inspiration)
- [7. Lizenz](#7-lizenz)

---

Eine interaktive, leichtgewichtige Web-Anwendung zur Auswertung und Verwaltung der **Travemünder Beach Open** (TGR Rangenberg).  
Entwickelt mit **Python** und **Streamlit**, erfordert keine externe Datenbank – alle Daten werden lokal gespeichert.  
Das Projekt befindet sich in der Entwicklung und ist noch nicht vollständig abgeschlossen.

---

## 1. Features

### 1.1 Turnierkonfiguration
- Definieren von Turniertypen (z. B. Damen, Herren, Quattro) mit:
  - Spieltag
  - Netzhöhe
  - Anzahl verfügbarer Felder

### 1.2 Neues Turnier
- **Anmeldedaten importieren** aus CSV oder XLSX
- Auswahl des Turniertyps
- Bearbeitung der Teilnehmerliste (Hinzufügen, Löschen, Ändern)
- **Automatische Gruppenbildung**:
  - Festlegung der Größe der Gruppen
  - Auswahl der Gruppenköpfe
  - Vereinsbasierte Verteilung: Teams aus demselben Verein werden, soweit möglich, in verschiedene Gruppen aufgeteilt
  - Automatische Zuweisung von Feldern zu Gruppen
- Einstellung des Spielmodus für vollständige und unvollständige Gruppen

### 1.3 Vorrunde
#### Übersicht
- Auswahl des Turniers
- Nachträgliche Anpassung der Gruppenverteilung
- Berücksichtigung verspäteter Teams (spätere Spielzeiten)
- Generierung von Spielprotokollen im HTML-Format (für Druck oder Weitergabe)

#### Ergebnisse
- Eintragen der Ergebnisse
- Anzeigen der Tabellen für jede Gruppe

#### Zusammenfassung
- Übersichtsseite
  - Gesamttabelle
  - Eigene Tabellen für jede Platzierung

#### Nächste Runde
- Noch in Entwicklung
- Konfiguration der nächsten Runden mit Übersicht

---

## 2. Voraussetzungen

Dieses Projekt erfordert **Python 3.13** (oder höher), da es moderne Sprachfeatures und Bibliotheken nutzt, die in älteren Versionen nicht verfügbar sind.  
Die folgende Anleitung ist für Windows-Systeme optimiert.

> ✅ Wenn Python bereits installiert ist, kannst du direkt mit [2.2 Herunterladen des Repositorys](#22-herunterladen-des-repositorys) fortfahren.

---

### 2.1 Installation von Python 3.13

1. Gehe zu: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Direkter Link zu [Python 3.13.15](https://www.python.org/downloads/release/python-31315/)
2. Lade die **Windows-Installer (64-Bit)** herunter (z. B. `python-3.13.15-amd64.exe`)
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

### 2.2 Herunterladen des Repositorys

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

    [Weiter mit: 3. Einrichten der App](#3-einrichten-der-app)

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
6. **Lösche der Einfachheit halber die oberste Ordner-Ebene** und benenne den Ordner `tbo-main` in `tbo` um. damit die Struktur wie folgt aussieht:
   ```
   tbo/
   ├── .streamlit/
   ├── assets/
   ├── data/
   ├── src/
   └── ...
   ``` 
   Dies ist nicht unbedingt notwendig, aber macht es übersichtlicher.


7. Gehe in den Ordner `tbo` und öffne ein Terminal (rechte Maustaste → „In Terminal öffnen“). Den Pfad, welchen du nun siehst, sollte auf `tbo` enden. 
    
    Die folgenden Anweisungen müssen in dieses Terminal hinkopiert und ausgeführt werden.

---

## 3. Einrichten der App

1. Erstelle eine virtuelle Umgebung (empfohlen):
   ```bash
   python -m venv .venv
   ```

2. Aktiviere die virtuelle Umgebung:
   ```bash
   .venv\Scripts\activate
   ```

   **Falls ein Fehler erscheint** (z. B. „Execution Policy“), führe Folgendes aus und wiederhole den vorherigen Schritt:

   ```bash
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. Installieren der benötigten Python Pakete:
   ```bash
   pip install .
   ```

---

## 4. Starten der App

Nach erfolgreicher Einrichtung kannst du die Anwendung starten:

1. **App ausführen:**
   ```bash
   streamlit run src/core/app.py
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

Wenn du die App später erneut starten möchtest:

1. Öffne den Ordner `tbo` in deinem Datei-Explorer.
2. Klicke mit der rechten Maustaste im Ordner auf einen leeren Bereich und wähle **„In Terminal öffnen“**.
3. Gib im Terminal folgenden Befehl ein:
    
    ```bash
    streamlit run src/core/app.py
    ```
---

## 5. Unterstützt von

- [TGR Rangenberg](https://www.tgr-rangenberg.de)

---

## 6. Inspiration

Das Grundgerüst und die Idee wurde übernommen von:

- [**sandly**](https://github.com/o3d1/sandly) – von o3d1

Und für das **Travemünder Beach Open** angepasst und erweitert.

---

## 7. Lizenz

Dieses Projekt ist unter der [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) lizenziert.  
Nutzung und Bearbeitung sind nur für **nicht-kommerzielle Zwecke** erlaubt – mit Namensnennung
