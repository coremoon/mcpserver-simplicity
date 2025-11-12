# Quick Start mit Poetry + Poethepoet

## Installation

### 1. Poetry installieren (falls noch nicht vorhanden)
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Linux/Mac
curl -sSL https://install.python-poetry.org | python3 -

# Oder via pip
pip install poetry
```

### 2. Projekt Setup
```bash
cd mcp-simplicity-server

# Dependencies installieren
poetry install

# Mit AI-Features (Claude)
poetry install --extras ai

# Oder mit poe
poetry run poe install
```

### 3. Poethepoet verwenden

```bash
# Alle verfügbaren Tasks anzeigen
poetry run poe

# Oder Poetry shell aktivieren
poetry shell

# Dann kannst du direkt poe verwenden:
poe
```

## 🚀 Häufige Workflows

### Server starten und testen
```bash
poetry shell
poe server          # Server starten
poe test            # Tests ausführen
```

### Agent verwenden
```bash
poetry shell
poe agent           # Regelbasierter Agent
poe agent-claude    # Claude Agent (benötigt API Key)
```

### Docker Workflow
```bash
poetry shell
poe docker-build    # Image bauen
poe docker-up       # Container starten
poe test-docker     # Tests gegen Docker
poe docker-logs     # Logs anschauen
poe docker-down     # Container stoppen
```

### Development
```bash
poetry shell
poe format          # Code formatieren
poe lint            # Code prüfen
poe test-all        # Alle Tests
```

## 📋 Wichtige Poe Tasks

```bash
# Setup & Installation
poe install         # Alle Dependencies installieren
poe setup           # Komplettes Setup (install + docker-build)

# Server & Tests
poe server          # MCP Server starten
poe test            # Lokale Tests
poe test-docker     # Docker Tests
poe test-all        # Alle Tests

# Agents
poe agent           # Regelbasierter Auto-Fix Agent
poe agent-claude    # Claude-basierter Agent
poe agent-docker    # Agent gegen Docker

# Docker
poe docker-build    # Docker Image bauen
poe docker-up       # Container starten
poe docker-down     # Container stoppen
poe docker-logs     # Logs anzeigen

# Development
poe format          # Code mit Black formatieren
poe lint            # Code mit Ruff prüfen
poe clean           # Temp files löschen
poe dev             # Dev Environment starten

# Utilities
poe compile --file=examples/arithmetic.simf  # Einzelne Datei kompilieren
```

## 🎯 Schnellstart-Beispiele

### Beispiel 1: Erste Schritte
```bash
# Setup
poetry install
poetry shell

# Tests ausführen
poe test

# Ergebnis: Zeigt welche Beispiele kompilieren
```

### Beispiel 2: Agent verwenden
```bash
poetry shell

# Agent starten (versucht Code zu fixen)
poe agent

# Ergebnis: 
# - Kompiliert alle Beispiele
# - Versucht Fehler automatisch zu beheben
# - Speichert erfolgreiche Fixes als *_fixed.simf
```

### Beispiel 3: Mit Claude
```bash
# API Key setzen
export ANTHROPIC_API_KEY='your-key-here'

poetry shell

# Claude-Agent starten
poe agent-claude

# Ergebnis:
# - Nutzt Claude für intelligente Code-Analyse
# - Bessere Fixes als regelbasierter Agent
# - Gibt Erklärungen für Änderungen
```

### Beispiel 4: Docker Workflow
```bash
poetry shell

# Komplettes Setup
poe setup           # Installiert und baut Docker

# Server im Docker starten
poe docker-up

# Agent gegen Docker laufen lassen
poe agent-docker

# Logs checken
poe docker-logs

# Aufräumen
poe docker-down
```

## 🔧 Konfiguration

### Poetry Virtual Environment
```bash
# Poetry verwendet automatisch .venv im Projekt
# Aktivieren:
poetry shell

# Oder Commands direkt ausführen:
poetry run python server.py
poetry run poe test
```

### Environment Variables
```bash
# Für Claude Agent
export ANTHROPIC_API_KEY='your-api-key'

# Für Custom Config
export MCP_SERVER_PORT=8080
```

## ❓ Troubleshooting

### Problem: `poetry: command not found`
**Lösung:**
```bash
pip install poetry
# oder
curl -sSL https://install.python-poetry.org | python3 -
```

### Problem: `poe: command not found`
**Lösung:**
```bash
poetry shell  # Poetry shell aktivieren
# dann funktioniert poe
```

### Problem: Dependencies installieren fehl
**Lösung:**
```bash
poetry lock --no-update
poetry install
```

### Problem: pysimplicityhl nicht gefunden
**Lösung:**
```bash
# Prüfen ob installiert
poetry show pysimplicityhl

# Neu installieren
poetry install
```

## 📊 Task Übersicht

| Kategorie | Tasks |
|-----------|-------|
| **Setup** | `install`, `setup`, `clean` |
| **Server** | `server`, `test`, `test-docker`, `test-all` |
| **Agents** | `agent`, `agent-claude`, `agent-docker` |
| **Docker** | `docker-build`, `docker-up`, `docker-down`, `docker-logs` |
| **Dev** | `format`, `lint`, `dev` |
| **Custom** | `compile --file=<path>` |

## 🎓 Weiterführend

Siehe `README.md` für:
- Detaillierte Dokumentation
- API Referenz
- Beispiele
- Contributing Guidelines
