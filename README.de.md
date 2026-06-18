<div align="center">

### 🌐 Sprache

| 🇬🇧 [![English](https://img.shields.io/badge/English-EEF2F7?style=for-the-badge)](README.md) | 🇯🇵 [![日本語](https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-EEF2F7?style=for-the-badge)](README.ja.md) | 🇪🇸 [![Español](https://img.shields.io/badge/Espa%C3%B1ol-EEF2F7?style=for-the-badge)](README.es.md) | 🇸🇦 [![العربية](https://img.shields.io/badge/%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-EEF2F7?style=for-the-badge)](README.ar.md) | 🇫🇷 [![Français](https://img.shields.io/badge/Fran%C3%A7ais-EEF2F7?style=for-the-badge)](README.fr.md) | 🇩🇪 [![● Deutsch](https://img.shields.io/badge/%E2%97%8F%20Deutsch-5271FF?style=for-the-badge)](README.de.md) |
|:--:|:--:|:--:|:--:|:--:|:--:|

<sub>👆 Click your language to switch ・ クリックで言語を切り替え</sub>

<sub>🪟 **Unter Windows:** läuft nativ (Git muss im PATH sein) — für die vollständige Sicherheitsgarantie (Berechtigungssperre für temporäre Dateien) WSL2 verwenden.</sub>

---

# 🔍 Due Diligence Engine

### **Die KI in deiner IDE → Tech-DD-Analyst von Weltklasse**

<sub>**Keine API-Schlüssel · PDF-First · OSS · CodeQL-geprüft**</sub>

<br/>

```
┌─────────────────────────────────────────────────────────────┐
│  $ dde prompt --pdf                                         │
│                                                             │
│  🌐 Live web research (2026 competitors, funding, CVEs)...  │
│  Reading codebase...                                        │
│  Evaluating across 5 dimensions (equal 20% weights)...      │
│  Building competitive landscape (7 charts × 6 markets)...   │
│  Researching implementation matrix (30 items × 10 cos.)...  │
│  Writing competitor selection rationales (with sources)...  │
│                                                             │
│  Score:  [■■■■■■■■■■■■■■■■■■■■■■■■■■□□□□] 82/100  Lv.8     │
│  Grade:  B  →  Viable with conditions                       │
│                                                             │
│  → ~/Downloads/dde_consulting_<project>_<date>.pdf  (24 p.) │
└─────────────────────────────────────────────────────────────┘
```

<br/>

[![License](https://img.shields.io/badge/License-Apache_2.0-000000.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-5271FF.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CodeQL](https://img.shields.io/badge/Security-CodeQL_·_Dependabot_·_pip--audit-5271FF.svg?style=for-the-badge&logo=github&logoColor=white)](SECURITY.md)
[![PDF](https://img.shields.io/badge/Output-PDF_First-000000.svg?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](#)

[![GitHub stars](https://img.shields.io/github/stars/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=5271FF)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=000000)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=5271FF)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/commits/main)
[![Version](https://img.shields.io/badge/version-v0.4.0-000000?style=flat-square)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/releases)

[![Repo Views](https://komarev.com/ghpvc/?username=taka-avantgarde&repo=Due-diligence-engine&color=5271FF&style=flat-square&label=Repo+Views)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine)

</div>

---

## ⚡ Schnellstart

**Einmalig installieren:**

```bash
python3 -m pip install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

**Aus deinem Projektverzeichnis ausführen:**

```bash
dde prompt --pdf
```

Verwende ein beliebiges KI-gestütztes IDE-Terminal (Claude Code / Cursor / Copilot). Deine KI liest den Code, bewertet ihn wie ein Technologieberater von Weltklasse und schreibt ein 24-seitiges PDF nach `~/Downloads/`. **Keine API-Schlüssel. Keine Cloud. Keine Zusatzkosten.**

<details>
<summary><sub>Weitere Installationsoptionen · Hinweis zu macOS Homebrew</sub></summary>

Kurzform für Linux / venv / ältere macOS-Versionen:
```bash
pip3 install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

macOS-Homebrew-Nutzer: verwende `python3 -m pip` — der reine `pip`-Befehl wird von Homebrew Python 3.12+ nicht mehr installiert.

</details>

---

## 💭 So erzielst du die besten Ergebnisse

> **Kurzfassung**: Starte die leistungsstärkste KI, auf die du in deinem IDE-Terminal Zugriff hast,
> füge den Befehl ein und warte 10–20 Minuten. Das war's.

**Empfohlenes Setup:**

- **Starte das leistungsfähigste verfügbare Modell** in deiner IDE (Claude Fable 5, GPT-5, Gemini 2.5 Pro usw.)
- **Füge `dde prompt --pdf`** in das Terminal ein
- **Hol dir einen Kaffee** ☕ — die KI liest Hunderte von Dateien, bewertet über
  9+ Dimensionen, recherchiert weltweit 5–10 Wettbewerber und erstellt ein 24-seitiges Beratungs-PDF
- **Erwartete Dauer**: **10–20 Minuten** (länger bei großen Codebasen oder tiefer arbeitenden Modellen)

**Warum dieser Ansatz?**

| Bedenken | Antwort |
|---------|--------|
| 🔐 **Datenabfluss?** | Keiner. Alles läuft innerhalb der KI-Sandbox deiner IDE — keine Drittanbieter-Server, keine Telemetrie. DDE selbst ist zu 100 % lokales Python |
| 💰 **Kosten?** | $0 zusätzlich. Nutzt dein bestehendes IDE-KI-Abonnement |
| 🔑 **API-Schlüssel?** | Nicht erforderlich. Deine IDE übernimmt die KI-Authentifizierung bereits |
| ⚙️ **Einrichtung?** | Nur `python3 -m pip install`. Keine Konfiguration, keine Accounts |
| 🎁 **Haken?** | Es gibt keinen. DDE ist ein **Hobby-Projekt** — aus Spaß gebaut und Open Source gemacht. Nutze es frei |

> **Von einem Solo-Entwickler als Hobby erstellt.** Wenn es dir hilft, ist das Belohnung genug. Gib dem Repo einen Stern, wenn es dir gefällt ⭐

---

## 💻 Wo läuft DDE — Nutze die KI, die du bereits hast

DDE erzeugt einen strukturierten Prompt. **Jeder KI-Agent, der Dateien lesen und Shell-Befehle ausführen kann**, kann ihn ausführen. Keine DDE-spezifische Integration, kein Plugin und kein Login erforderlich.

**Verifiziert funktionsfähig** (offizielle Doku + getestet, 2026-05):
- ✅ [**Claude Code**](https://code.claude.com/docs/en/overview) (CLI / VS Code / JetBrains / Desktop / Web — offiziell von Anthropic)
- ✅ [**GitHub Copilot Agent Mode**](https://docs.github.com/en/copilot/using-github-copilot/copilot-chat/asking-github-copilot-questions-in-your-ide) (VS Code / Visual Studio / JetBrains / Xcode / Eclipse — allgemein verfügbar)

**Sollte funktionieren** (Anforderungen: Datei lesen + Shell-Ausführung + idealerweise Websuche):
- Cursor Agent, Gemini Code Assist, Continue.dev, Cody (Sourcegraph), Aider, Windsurf, Amazon Q Developer, JetBrains AI Assistant und ähnliche agentische Terminals.

> ✅ Wenn du bereits eines der oben genannten nutzt, bist du nur ein `pip install` davon entfernt, DDE noch heute auszuführen.
> Einen bestimmten Terminal als funktionsfähig bestätigt? Sag uns in einem [Issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues) Bescheid.

### 💰 Keine Zusatzkosten

**Du zahlst nur für das KI-Abonnement, das du ohnehin schon hast.** Claude Code Pro / GitHub Copilot / Cursor Pro / Gemini Advanced — DDE läuft im Rahmen des Kontingents deiner bestehenden KI. Keine DDE-Preisstufen, keine zusätzlichen API-Schlüssel, niemals versteckte Gebühren.

---

## 👥 Für wen ist das?

| Nutzer | Anwendungsfall | Zeitersparnis |
|------|----------|-----------|
| **VC-Tech-Partner** | Technische DD vor Investments bei Portfolio-Kandidaten | 2–5 Tage → 30 Min |
| **CTOs / Engineering-Leads** | Interne Tech-Prüfung vor Vorstandssitzungen | 1 Woche → 1 Stunde |
| **M&A-Tech-Berater** | Due Diligence bei Übernahmezielen | 1–2 Wochen → 1 Tag |
| **Unabhängige DD-Berater** | Tech-Bewertungen für Boutique-Firmen | Skalierung: 1→10 Kunden/Woche |
| **Gründer** | Selbsteinschätzung vor der Finanzierungsrunde | objektiver Blick auf die eigene Codebasis |
| **Corporate Innovation** | Bewertung von Anbieter-/Startup-Partnerschaften | ad-hoc → systematisch |

> Gebaut für Ingenieure und technische Entscheider, die KI bereits in ihrem täglichen Arbeitsablauf nutzen.

---

## 🆚 vs. Andere Tools

|   | DDE | Manuelle DD | Generisches KI-Code-Review | SaaS-DD-Plattformen |
|---|:---:|:---:|:---:|:---:|
| **Kosten** | $0 (nutzt deine IDE-KI) | $$$$ (Beraterhonorare) | API-Gebühren | $$$$ (Abonnement) |
| **Datenschutz** | Nur lokal | Lokal | Sendet Code an Anbieter | Sendet Code an Anbieter |
| **Ausgabe** | 24-seitiges Beratungs-PDF | Individueller Bericht | Inline-Kommentare | Web-Dashboard |
| **Datenaktualität** | ✅ Live-Websuche (2026) + Quellen-URLs | Hängt vom Analysten ab | Nur Trainingsdaten (veraltet) | Vom Anbieter gesteuerte Aktualisierung |
| **Krypto-Tiefe** | Niveau von PQXDH / Signal Protocol | Hängt vom Berater ab | Generisch | Generisch |
| **Wettbewerbs-Charts** | 7 + Implementierungsmatrix | Manuelle Recherche | Keine | Begrenzt |
| **Einrichtungszeit** | 1 Befehl | Wochen | Minuten | Tage (Account/Onboarding) |
| **Anpassbarkeit** | Voller Quellcode-Zugriff | Ja | Begrenzt | Anbieter-gebunden |

---

## Was DDE anders macht

Die meisten „KI-Code-Reviewer" prüfen:
> *„Hat es Authentifizierung? ✓ Hat es HTTPS? ✓ Hat es Tests? ✓"*

Das ist Häkchen-Compliance. **DDE geht tiefer:**

> *„Ist die Verschlüsselung das Signal Protocol? Ist es PQXDH mit ML-KEM-1024?
> Basiert es auf libsignal/BoringSSL-FFI oder auf selbstgebauter Kryptografie?
> Veröffentlicht das Team kryptografische Forschung?"*

Aufgebaut auf der **Atlas Engineering Philosophy**: ernsthaftes Cybersicherheits-Engineering
über Verschlüsselung, Datenschutz, Kommunikation und mehrschichtige Verteidigung hinweg — direkt
aus dem Quellcode gelesen. Häkchen-Compliance (SOC2, MFA, WebAuthn-Zertifizierungen)
dient nur als Referenz und wird nie bewertet.

**🌐 Neu in v0.3.2**: Bevor überhaupt Code gelesen wird, führt die KI **Live-Websuchen** für die aktuellste Wettbewerbslandschaft (Übernahmen, Einstellungen, neue Marktteilnehmer), Finanzierungsrunden 2026, jüngste CVEs und regulatorische Veränderungen durch. Jeder Wettbewerber und jede Zelle der Implementierungsmatrix trägt eine **Quellen-URL + ein Verifizierungsdatum**, und die JSON-Ausgabe beginnt mit einem `data_freshness`-Block, der jede Suchanfrage protokolliert. **Veraltete Analysen, die nur auf dem Trainingsstichtag beruhen, sind strukturell ausgeschlossen.**

---

## 🔒 Atlas Engineering Philosophy (cybersicherheitsorientierte Parallelansicht)

Ein paralleles Bewertungssystem, ergänzend zur standardmäßigen 5-Dimensionen-Bewertung.

```
4 axes — weights sum to 100%

  Performance        20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  Stability          20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  Lightweight         5%  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  Security Strength 55%  ███████████████████████████░░░░░  ← THE CORE

  Cybersecurity sub-breakdown (within 55% — defense across all layers):
    Cryptographic Sophistication  35%  ← largest: Signal Protocol, PQXDH, libsignal
    Privacy Protection             8%
    Communication Safety           7%
    Layer Composition              3%
    Basic Hygiene (MFA/WebAuthn)   2%  ← code-only; certs are reference-only
```

---

## 📊 5-Dimensionen-Standardbewertung (v0.3 — ausgewogen, gleiche Gewichte)

| Dimension | Gewicht | Was sie erkennt |
|-----------|-------:|-----------------|
| Technische Originalität | 20% | API-Wrapper vs. echtes geistiges Eigentum |
| Technologische Fortschrittlichkeit | 20% | Modernität des Stacks |
| Implementierungstiefe | 20% | PoC vs. Produktion |
| Architekturqualität (inkl. Sicherheitslage) | 20% | Strukturqualität + Sicherheitsreife |
| Konsistenz der Behauptungen | 20% | Pitch vs. Realität |

> **Endpunktzahl** = Heuristische Analyse (30 %) + KI-Durchschnittswert (70 %)

> **Änderung in v0.3**: Die Sicherheitslage wurde in die Architekturqualität integriert. Sicherheit wird nun als integraler Bestandteil einer produktionsreifen Architektur bewertet, nicht als eigenes Silo.

```
Grade Bands:

  0      40       60      75       90     100
  |------|--------|-------|--------|------|
   F      D        C       B        A
   ✗      ⚠        ⚡       ✓        ★
```

| Note | Empfehlung |
|-------|----------------|
| ★ A (90+)  | Starker Investitionskandidat |
| ✓ B (75–89)| Tragfähig unter Bedingungen |
| ⚡ C (60–74)| Erhebliche Bedenken |
| ⚠ D (40–59) | Hohes Risiko |
| ✗ F (<40)  | Nicht investieren |

Jede Dimension wird zusätzlich mit **Lv.1–10** anhand expliziter Kriterien bewertet.

---

## 🎯 7 Wettbewerbs-Charts × 6 Märkte

Für jeden der 6 globalen Märkte (Global / US / EMEA / Japan / SEA / LATAM):

| # | Chart | Was es zeigt |
|---|-------|---------------|
| 1 | **Forrester Wave / Magic Quadrant** | Vision × Umsetzung |
| 2 | **BCG-Wachstums-Marktanteils-Matrix** | Marktwachstum × relativer Anteil |
| 3 | **McKinsey Tech Moat** | Wettbewerbsposition × technischer Burggraben |
| 4 | **Sicherheits- & Datenschutzreife** | Sicherheitsimplementierung × Datenschutzbereitschaft |
| 5 | **Data Governance & Transparenz** | Datenschutz × Audit-Transparenz |
| 6 | **GS risikoadjustierte Rendite** | Abwärtsrisiko × Aufwärtspotenzial |
| 7 | **Innovation vs. Kommerzialisierung** | F&E-Geschwindigkeit × ARR-Traktion (3D-Blase) |

**6–16 Wettbewerber pro Chart** mit Begründungs-Beschriftungen der Achsen, die erklären,
*warum* jede Achse wichtig ist und *was* der zusammengesetzte Score erfasst.

---

## 🆕 Implementierungsfähigkeits-Matrix

Das 8. Wettbewerbs-Chart — **~30 Punkte × 5–10 globale Top-Wettbewerber**:

```
                        Target   Comp. A   Comp. B   Comp. C   Comp. D   ...
Encryption (core differentiator)
  Feature 1              ○        ○         ×         △         ○
  Feature 2              ○        ○         ×         ×         ○
  Feature 3              ○        ○         ○         ×         ○
  Feature 4              ○        ×         ×         △         △
  ...
Privacy & Compliance
  Feature 1              ○        △         ○         ×         △
  Feature 2              ○        ○         △         ×         ×
  ...
```

Punkte und Wettbewerber werden **dynamisch je nach Branche des Ziels** ausgewählt
(Messaging, Fintech, Medizin, Gaming, SaaS, IoT usw.).

4-Status-Kennzeichnung (japanischer Tech-Bewertungsstandard):
- **○ verifiziert** (öffentlich dokumentierte Implementierung)
- **△ behauptet** (behauptet, nicht überprüfbar)
- **× nicht implementiert** (ausdrücklich nicht vorhanden)
- **? unbekannt** (nicht bestimmbar — wird dem Raten vorgezogen)

Plus **Begründungen zur Wettbewerberauswahl** — je 3–5 Zeilen, die erklären, warum jeder
bestimmte Wettbewerber als Vergleichsziel gewählt wurde (Hauptsitz, Marktposition, Kategorie).

---

## 📄 Was im 24-seitigen PDF steckt

| # | Abschnitt | Inhalt |
|---|---------|---------|
| 1 | Titelseite | Schwarz + Arc-Sky-Akzent (#5271FF), Projektname, Score, Note |
| 2 | Score-Dashboard | **5-Dim**-Balkendiagramm (je 20 %) + Score-Barometer |
| 3 | Executive Summary | Geschäftliche + technische Zusammenfassung |
| 4 | SWOT-Analyse | 2×2-Visualraster mit Belegen + Geschäftsanalogien |
| 5 | Score-Aufschlüsselung | Begründung & Treiber je Dimension |
| 6 | Tech-Level-Bewertung | **5-Dim**-Lv.1–10-Balkendiagramm + Gesamtanzeige |
| 7 | Zukunftsausblick | 1/3/5-Jahres-Prognosen mit Konfidenz |
| 8 | Strategische Beratung | Sofort-, mittel- und langfristig |
| 9 | Investment Thesis | Empfehlung, Risiken, Aufwärtspotenzial, Vergleichswerte |
| 10 | Red Flags | Nach Schweregrad bewertet (Kritisch/Hoch/Mittel/Niedrig) |
| 11 | Site-Verifizierung | 10-Punkte-Audit der technischen Leistungsfähigkeit (4 Behauptung-vs-Code + 6 codemessbar) |
| 12-14 | Wettbewerbsanalyse | 7 Charts × 6 Märkte mit Achsenbegründung |
| 15 | **🆕 Begründungen zur Wettbewerberauswahl** | 3–5 Zeilen Erläuterung je Wettbewerber (warum gewählt, Hauptsitz, Position) |
| 16 | **Implementierungsfähigkeits-Matrix** | ~30 Punkte × Top-Wettbewerber, ○△×?-Kennzeichnung |
| 17 | **Atlas-4-Achsen-Dashboard** | Performance / Stabilität / Leichtgewichtigkeit / Sicherheitsstärke |
| 18 | **Sicherheits-Unteraufschlüsselung + Glossar** | 5 Unterpunkte mit Glossar für Nicht-Techniker (MFA/SOC2/libsignal/PQXDH…) |
| 19-24 | Glossar · Konsistenz · Kosten · Lösch-Zertifikat | Standard-Anhangabschnitte |

---

## 🛠️ Verwendung

```bash
# Current directory, English PDF
dde prompt --pdf

# Japanese PDF
dde prompt --pdf --lang ja

# GitHub repo with stage context
dde prompt owner/repo --pdf --lang ja --stage seed

# Non-interactive (for AI terminals without prompt support)
dde prompt --pdf --lang ja \
  --url https://example.com \
  --url https://docs.example.com

# Direct BYOK multi-AI cross-verification (optional)
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_AI_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
dde analyze owner/repo
```

---

## 🔐 Sicherheits- & OSS-Philosophie

| Garantie | Umsetzung |
|-----------|----------------|
| **Nur lokale Verarbeitung** | `dde prompt` sendet niemals Daten irgendwohin |
| **Kein Quellcode in Berichten** | PDFs enthalten ausschließlich Befunde |
| **API-0-Tage-Aufbewahrung** | `dde analyze` nutzt No-Retention-Endpunkte |
| **Automatisierte Sicherheits-CI** | CodeQL · Dependabot · pip-audit · safety · osv-scanner · GitHub Secret Scanning |
| **Branch-Schutz** | `main` erfordert PR + CI + Secret-Push-Schutz |
| **Privater Repo-Zugriff via PAT** | Einmalig im Speicher verwendet, nie gespeichert |

Schwachstellenmeldungen: siehe [SECURITY.md](SECURITY.md) — 48-Stunden-Reaktions-SLA.

### Warum OSS ein Sicherheitsmerkmal ist, kein Risiko

Open Source bedeutet, dass jede Zeile überprüfbar ist. Keine versteckten Hintertüren. Kein Black-Box-Scoring.
Das ist dieselbe Philosophie wie bei Signal und libsignal: **Transparenz *ist* Vertrauen**.

---

## ❓ FAQ

**F: Sendet DDE meinen Code irgendwohin?**
A: Nein. `dde prompt` läuft vollständig lokal — es erzeugt einen strukturierten Prompt, den die KI deiner IDE liest. Die KI bewertet den Code an Ort und Stelle. Das optionale `dde analyze` (BYOK) sendet nur über die No-Retention-Endpunkte der KI-Anbieter.

**F: Warum ist es kostenlos? Wo ist der Haken?**
A: Es gibt keinen Haken. DDE ist OSS (Apache 2.0) und nutzt dein bestehendes IDE-KI-Abonnement (Claude Code / Cursor / Copilot). Keine Telemetrie, kein Upselling.

**F: Kann ich es in der CI nutzen?**
A: Ja — siehe [`action.yml`](action.yml). Füge die GitHub Action zu PRs hinzu für automatisiertes DD-Scoring.

**F: Wie genau sind die Wettbewerbs-Charts?**
A: Charts werden von der KI aus öffentlichen Quellen recherchiert (Whitepapers, GitHub, Blogs, SOC2-Berichte). Die Konfidenz hängt von der Transparenz der Wettbewerber ab. Verwende `?` (unbekannt) großzügig — Falschpositive schaden der Glaubwürdigkeit mehr als Lücken.

**F: Sind Wettbewerberdaten nicht veraltet? KI-Trainingsstichtage sind 6–12 Monate alt.**
A: Seit v0.3.2 ist **SCHRITT 0 „Live Web Research" verpflichtend**. Bevor überhaupt Code gelesen wird, führt die KI WebSearch / WebFetch für Wettbewerber-Bewegungen 2025–2026 (Übernahmen, Einstellungen, neue Marktteilnehmer), aktuellste Finanzierungsrunden, CVEs und regulatorische Veränderungen durch. Jeder Wettbewerber und jede Matrixzelle trägt ein `sources`- (URL) und `last_verified`-Feld (Datum), und die JSON-Ausgabe beginnt mit einem `data_freshness`-Block, der jede ausgeführte Suchanfrage protokolliert. Fehlen der Laufzeitumgebung Websuch-Tools, MUSS die KI eine `data_cutoff_warning` schreiben — **per Design keine stillschweigend veraltete Ausgabe**.

**F: Warum „Atlas Engineering Philosophy"?**
A: DDE wird von **Atlas Associates Inc** entwickelt, der Firma hinter Arc Messenger (E2EE-Messaging mit libsignal + PQXDH). Die 4-Achsen-Bewertung spiegelt wider, worauf wir bei der Tech-Bewertung tatsächlich achten.

**F: Kann ich die Bewertungsgewichte anpassen?**
A: Die 5-Dimensionen-Gewichte sind jeweils gleich 20 % (ausgewogen, einfach, interpretierbar). Die Atlas-4-Achsen-Gewichte (20/20/5/55) spiegeln die Atlas-Philosophie wider und sind ebenfalls fest. Die Unterpunkt-Gewichte innerhalb der Sicherheitsstärke passen sich dem Branchenkontext an.

**F: Was, wenn mein Projekt nicht sicherheitskritisch ist?**
A: Der 5-Dimensionen-Score (Architekturqualität enthält die Sicherheitslage mit ausgewogenen 20 %) ist dein primärer Score. Die Atlas-4-Achsen sind eine parallele Referenzansicht — beide werden angezeigt.

**F: Ich bekomme `command not found: pip` — wie installiere ich?**
A: Verwende stattdessen `python3 -m pip install ...`. macOS Homebrew Python 3.12+ liefert keinen reinen `pip`-Befehl mehr aus. Die Form `python3 -m pip` funktioniert auf allen Plattformen (macOS / Linux / Windows / venv / pyenv / conda).

**F: Warum beeinflussen Drittanbieter-Zertifizierungen (SOC2, ISO, HIPAA) den Score nicht?**
A: DDE bewertet den Quellcode, nicht das Abzeichen. Ein SOC2-zertifizierter Dienst mit Klartext-Speicherung hat immer noch Klartext-Speicherung. Ein nicht zertifizierter libsignal+PQXDH-Dienst ist kryptografisch dennoch stark. Zertifizierungen werden zum Kontext angezeigt, aber nie bewertet — siehe die Seite zur Sicherheits-Unteraufschlüsselung.

---

## 🗺️ Roadmap

**Kürzlich ausgeliefert (v0.3.x)**
- ✅ **PDF-Berichte in 14 Sprachen** (2026-06, v0.4.0): Das Beratungs-PDF wird über `--lang` in 14 Sprachen erzeugt — English / 日本語 / Español / Français / Deutsch / Português / Nederlands / Italiano / Bahasa Indonesia / 简体中文 / 한국어 / Tiếng Việt / ไทย / العربية (Arabisch mit kontextueller RTL-Formung). Gebündelte Noto-Schriften, keine Einrichtung.
- ✅ **Windows-Kompatibilitätskorrekturen** (2026-06, v0.3.8): plattformübergreifender temporärer Pfad für den `--pdf`-Beratungsablauf (zuvor fest codiertes `/tmp`) und Windows-Zwischenablage-Unterstützung (`clip`) für `--copy`
- ✅ **READMEs in 6 Sprachen** (2026-06, v0.3.7): Sprachumschalter am Seitenanfang mit hervorgehobener aktiver Sprache — English / 日本語 / Español / العربية / Français / Deutsch, jeweils ein separates `README.<lang>.md`
- ✅ **Upgrade auf Claude Fable 5** (2026-06, v0.3.6): Judge-Tier von Opus 4.8 → **Fable 5** (`claude-fable-5`, Anthropics leistungsfähigstes breit veröffentlichtes Modell, GA 2026-06-09). Tier-Schlüssel umbenannt `opus` → `fable`. Preise $10/$50 pro MTok (2× Opus 4.8, mit Priorität auf der Qualität des Endurteils)
- ✅ **PDF-Chart-Feinschliff + Behebung von Label-Überlappungen** (2026-05, v0.3.5): alle Balken in den Charts Score-Dashboard / Tech-Level / Wettbewerb / Matrix wurden als moderne, abgerundete Pillenformen neu gestaltet. Lange japanische Labels (z. B. 「アーキテクチャ品質（セキュリティ含む）」), die die Balken überlappten, sind durch Verbreitern des Label-Bereichs behoben (verifiziert durch Rendern + visuelle Prüfung jeder PDF-Seite)
- ✅ **Upgrade auf Claude Opus 4.8** (2026-05, v0.3.3–4): Judge-Tier von Opus 4.7→4.8 (Sonnet 4.6 / Haiku 4.5 ebenfalls aktualisiert). Vermeidet die Abschaltung des Legacy-Opus-4 / Sonnet-4 (20250514) am 2026-06-15 und spiegelt die Opus-Preissenkung ($15→$5 Input) wider
- ✅ **Transfer in die Atlas-Associates-Inc-Org** (2026-05, v0.3.4–5): Repo verschoben taka-avantgarde → Atlas-Associates-Inc. Alle URLs aktualisiert, Autoren-Credit vereinheitlicht auf Takayuki Miyano (@taka-avantgarde) + Atlas Associates Inc, gitleaks → GitHub-natives Secret Scanning
- ✅ **Live-Web-Research-Pflicht** (2026-05, SCHRITT 0): `_WEB_RESEARCH_MANDATE` an den Anfang jedes Beratungs-Prompts hinzugefügt — die KI MUSS WebSearch/WebFetch zur Wettbewerbslandschaft, Finanzierung, Tech-Trends, CVEs und Regulierung **vor** dem Lesen von Code ausführen. Die JSON-Ausgabe enthält nun einen `data_freshness`-Block (Suchdatum, ausgeführte Suchanfragen, konsultierte Quellen) plus `sources` / `last_verified`-Felder je Wettbewerber und je Matrixzelle. Beseitigt veraltete Analysen, die nur auf dem Trainingsstichtag beruhen
- ✅ **Behebung von Prompt-Tippfehlern**: „6 dimensions" → „5 dimensions" und „5つのチャート" → „7つのチャート" im JA-Beratungs-Prompt
- ✅ **CI-Selbsttest-Fix** (2026-05): `grep -c` in `action.yml` gab bei null Treffern den Exit-Code 1 zurück, was `set -e` + `pipefail` als Job-Fehlschlag weitergaben. Behoben mit dem Muster `|| FALLBACK="0"`. **Der DDE-Selbsttest ist jetzt zum ersten Mal grün**
- ✅ **Bewertungsformel im README explizit gemacht** (Endpunktzahl = Heuristik 30 % + KI-Durchschnitt 70 %)
- ✅ **Dependabot vollständig verdrahtet**: Labels `dependencies` / `security` / `ci` erstellt und PR #23 (checkout v6) / #24 (upload-artifact v7) / #25 (osv-scanner-action v2.3.8) gemergt
- ✅ **Schutzleitplanken gegen Eigen-Bias**: explizite Warnungen „das Ziel ist NICHT DDE selbst" im Prompt-Header (verhindert KI-Verwechslung, wenn DDE auf einem anderen Projekt ausgeführt wird)
- ✅ **Red Flags klargestellt**: dargestellt als umsetzbare Punkte zur Codeverbesserung (NICHT in den Score einbezogen)
- ✅ **Schnellstart vereinfacht** im README (einzelner Installationsbefehl + ausklappbare Alternativen)
- ✅ **Atlas-Philosophie neu gerahmt** als „Cybersicherheitsverteidigung insgesamt" (nicht nur Verschlüsselung — Verschlüsselung ist mit 35 % das größte Untergewicht)
- ✅ **Site-Verifizierung auf reine technische Leistungsfähigkeit fokussiert** (10 Punkte: 4 Behauptung-vs-Code + 6 codemessbar — Krypto-Tiefe, Nebenläufigkeitsmodell, I/O-Muster, Caching, Skalierbarkeit, ML-Tiefe)
- ✅ Atlas-Gewichte neu ausbalanciert auf **20 / 20 / 5 / 55** (Verschlüsselungskern auf 35 % angehoben)
- ✅ **Bewertung nur anhand des Quellcodes**: Drittanbieter-Zertifizierungen (SOC2 / ISO / HIPAA) dienen nur als Referenz, werden nicht bewertet
- ✅ **1:1-Zuordnung der Wettbewerber** zwischen Matrix und Begründungen (geschätzter Score je Wettbewerber + Haftungsausschluss zu öffentlichen Informationen)
- ✅ 5-Dimensionen-Bewertung (gleiche 20 %-Gewichte, Sicherheit in die Architektur integriert)
- ✅ Begründungen zur Wettbewerberauswahl (3–5 Zeilen Erläuterung je Wettbewerber)
- ✅ Glossar für Nicht-Techniker auf der Seite zur Sicherheits-Unteraufschlüsselung (MFA/SOC2/libsignal/PQXDH)
- ✅ Haltung im AIDD-Zeitalter: keine Abwertung für KI-Nutzung oder Commits mit hoher Geschwindigkeit
- ✅ `python3 -m pip`-Anleitung + Besucherzähler-Badges
- ✅ PDF-Layout-Fixes: KeepTogether, KeepInFrame (SWOT), zweizeilig umgebrochene Beschreibungen

**Zuvor ausgeliefert (v0.2.0)**
- ✅ Atlas-4-Achsen-Optimierungsbewertung (ursprünglich 25/20/5/50, jetzt 20/20/5/55)
- ✅ Implementierungsfähigkeits-Matrix (8. Wettbewerbs-Chart)
- ✅ Web-Dashboard vollständig entfernt (nur CLI + PDF)
- ✅ Markenidentität Schwarz + Arc Sky (#5271FF)
- ✅ Überarbeitung des Typografie-Systems (Zeilenabstand, Hierarchie)
- ✅ Härtung der Sicherheits-CI (CodeQL, Dependabot, gitleaks)

**Geplant (v0.4.0+)**
- 🚧 Batch-Modus — ein Portfolio von Repos mit einem Befehl analysieren
- 🚧 Verlaufsverfolgung — erneut analysieren und Score-Differenzen über die Zeit anzeigen
- 🚧 Slack/Discord-Benachrichtigungsadapter
- 🚧 Branchenspezifische Bewertungspakete (Voreinstellungen für Medizin, Fintech, Gaming)
- 🚧 Vertrieb über PyPI / Homebrew

Öffne ein [Issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues), um Funktionen vorzuschlagen oder Fehler zu melden.

---

## 🤝 Mitwirken

Beiträge sind willkommen! Die Codebasis ist klein und gut getestet:

```bash
git clone https://github.com/Atlas-Associates-Inc/Due-diligence-engine
cd Due-diligence-engine
python3 -m pip install -e ".[dev]"
pytest
```

- **Fehlerberichte**: bitte die Ausgabe von `dde --version` und eine minimale Reproduktion beifügen
- **Funktionswünsche**: zunächst eine GitHub Discussion eröffnen, um das Interesse abzuschätzen
- **Pull Requests**: sicherstellen, dass alle Tests bestehen + neue Tests für neue Funktionen hinzufügen

---

## 📜 Lizenz

[Apache License 2.0](LICENSE) — Copyright © 2026 [Takayuki Miyano](https://github.com/taka-avantgarde) / [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

---

<div align="center">

**Powered by Due Diligence Engine**

Created by [Takayuki Miyano](https://github.com/taka-avantgarde) — [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

`v0.4.0` — 🌍 READMEs in 6 Sprachen · 🆕 Claude Fable 5 / Sonnet 4.6 / Haiku 4.5 · 🌐 Live-Websuche · 5-Dimensionen-Bewertung

</div>
