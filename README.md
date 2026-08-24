# 🏐 Travemünder Beach Open - Turnierauswertung

Eine interaktive, leichtgewichtige Web-Applikation zur Auswertung und Verwaltung der **Travemünder Beach Open** (TGR Rangenberg).  
Die App ist mit **Python** und **Streamlit** entwickelt und erfordert keine komplexe Datenbank – alle Daten werden lokal gespeichert.  
Das Projekt befindet sich in der Entwicklung und ist noch unvollständig.

---

## ✨ Features

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

## ✅ **Python 3.13 erforderlich**

Dieses Projekt erfordert **Python 3.13** (oder höher), da es moderne Sprachfeatures und Bibliotheken nutzt, die in älteren Versionen nicht verfügbar sind.

---

### 🛠️ **Installation von Python 3.13**

#### 🔹 **Windows**
1. Gehe zu: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    - Direkter Link zu [Python 3.13](https://www.python.org/downloads/release/python-31315/)
2. Lade die **Python 3.13.x**-Version herunter (z. B. `Windows installer (64-bit)` (die Datei heißt `python-3.13.15-amd64.exe`))
    - der Windows `Download Python install manager` ist nicht notwendig
3. Führe die Installation aus und **markiere die Option**:
   ```
   ✅ Add Python to PATH
   ```
4. Öffne ein neues Terminal (PowerShell oder CMD) und prüfe:
   ```bash
   python --version
   ```
---

## 🛠️ Installation

Die Installation ist in wenigen Schritten erledigt. Du benötigst lediglich **Python 3.13+** auf deinem System.
Gehe zu einem Ordner wo du das Projekt speichern möchtest.
Öffne die Terminal-Shell

1. **Terminal-Shell öffnen**

    Öffne den Datei-Explorer und gehe in ein Verzeichnis, wo du die Projektdaten speichern möchtest.

    Klicke mit der rechten Maustaste in dem Ordner auf eine leere Stelle und wähle „In Terminal öffnen“ aus dem Menü.
    Führe anschließen die folgenden Befehle in dem Terminal nacheinander aus.

2. **Repository klonen:**
   ```bash
   git clone https://github.com/johannhein/tbo.git
   cd tbo
   ```

3. **Virtuelle Umgebung erstellen (empfohlen) und aktivieren:**
   ```bash
   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows
   .venv\Scripts\activate
   ```

4. **Abhängigkeiten installieren:**
   ```bash
   pip install -e .
   ```

---

## 🚀 Getting Started

Sobald die Installation abgeschlossen ist, kannst du die Applikation lokal starten.

1. **App ausführen:**
   ```bash
   streamlit run src/main.py
   ```

2. **Im Browser öffnen:**
   Streamlit öffnet automatisch deinen Standard-Webbrowser unter `http://localhost:8501`.

3. **Turnier starten:**
   - Navigiere durch die oberen Tabs: **Voreinstellungen**, **Neues Turnier**, **Vorrunde**.

---

## 🤝 Unterstützt von

- [TGR Rangenberg](https://www.tgr-rangenberg.de)
- [Beachvolleyball-Community](https://www.beachvolleyball.de)

---

## 🎯 Inspiration & Attribution

Dieses Projekt wurde inspiriert von:
- [**sandly**](https://github.com/o3d1/sandly) – von o3d1

Wir haben die Kernkonzepte übernommen und für das **Travemünder Beach Open** angepasst.

---

## 📄 Lizenz

Dieses Projekt ist unter der [MIT-Lizenz](LICENSE) veröffentlicht.