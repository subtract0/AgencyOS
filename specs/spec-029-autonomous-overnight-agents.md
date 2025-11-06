# Spezifikation: Autonome Nachtwache (`/start-overnight-agents`)

**ID:** `spec-029-autonomous-overnight-agents`
**Status:** Entwurf
**Erstellt am:** 2025-10-12

## 1. Ziele

- **G1: Kontinuierliche Codebase-Verbesserung:** Einrichten eines autonomen Prozesses, der über Nacht wichtige Wartungs- und Refactoring-Aufgaben in der `AgencyOS`-Codebase durchführt.
- **G2: Verteilte Parallele Ausführung:** Nutzung der kombinierten Rechenleistung des MacBook Pro (current hardware) und MacBook Air (M4) für eine effiziente Abarbeitung.
- **G3: Nachvollziehbare Ergebnisse:** Jede abgeschlossene Mission wird in einem separaten, klar benannten Git-Branch isoliert, um eine einfache Überprüfung und ein sauberes Merging am nächsten Morgen zu ermöglichen.
- **G4: Einfache Konfiguration und Erweiterbarkeit:** Der Pool der auszuführenden Missionen soll leicht über eine Konfigurationsdatei verwaltet und erweitert werden können.

## 2. Personas

- **Entwickler:** Möchte sich auf die Entwicklung neuer Features konzentrieren und die Beseitigung technischer Schulden, die Verbesserung der Testabdeckung und die Aktualisierung der Dokumentation an ein autonomes System delegieren. Er erwartet am Morgen eine Liste von fertigen Pull-Requests zur Überprüfung.

## 3. Lösungsvorschlag: Architektur der "Nachtwache"

Die "Nachtwache" besteht aus drei Hauptkomponenten: einem Orchestrator, verteilten Workern und einer zentralen Aufgaben-Warteschlange.

### 3.1 Der Befehl `/start-overnight-agents`

Dies ist der Startpunkt. Er ruft das Orchestrator-Skript auf und übergibt Konfigurationsparameter.

**Argumente:**
- `--pro-threads <N>`: Anzahl der parallelen Worker auf dem current hardware (Standard: 2).
- `--air-threads <N>`: Anzahl der parallelen Worker auf dem M4 Air (Standard: 1).
- `--mission-set <name>`: Wählt ein vordefiniertes Set von Aufgaben (z.B. `refactoring`, `testing`, `docs`, `full`).

### 3.2 Der Orchestrator (`scripts/overnight_orchestrator.py`)

**Rolle:** Der "Vorarbeiter".

- Liest die auszuführenden Missionen aus `overnight_missions.json`.
- Erstellt eine zentrale Aufgaben-Warteschlange (`task_queue.json`) und sichert den Zugriff darauf mit einer Lock-Datei (`task_queue.lock`).
- Startet die lokalen Worker-Threads auf der primären Maschine.
- Gibt einen Befehl aus, der auf der sekundären Maschine (MacBook Air) ausgeführt werden kann, um zusätzliche Worker zu starten.

### 3.3 Die Worker (`scripts/overnight_worker.py`)

**Rolle:** Die "Arbeiter".

- Ein Worker-Prozess läuft in einer Schleife: Er sperrt die Queue, holt sich die nächste Aufgabe, gibt die Queue wieder frei.
- Für jede Aufgabe erstellt der Worker einen neuen Git-Branch (z.B. `night-watch/pydantic-migration-20251012-0015`).
- Er führt den in der Aufgabe definierten `/primeA`-Befehl aus.
- Nach erfolgreicher Ausführung (bestätigt durch einen grünen, sauberen Zustand) committet der Worker seine Arbeit in den Branch.
- Er meldet den Status der Aufgabe (Erfolg/Fehler) an den Orchestrator zurück.

## 4. Akzeptanzkriterien

- [ ] Der Befehl `/start-overnight-agents` kann erfolgreich ausgeführt werden.
- [ ] Eine `task_queue.json` wird basierend auf einer Missions-Konfigurationsdatei erstellt.
- [ ] Worker-Prozesse auf mindestens zwei Maschinen können parallel und ohne Konflikte Aufgaben aus der Queue abarbeiten.
- [ ] Jede erfolgreich abgeschlossene `/primeA`-Mission resultiert in einem eindeutigen Git-Branch, der die durchgeführten Änderungen enthält.
- [ ] Der Orchestrator gibt am Ende einen Bericht über alle ausgeführten, fehlgeschlagenen und übersprungenen Aufgaben aus.

## 5. Implementierungsplan (TDD-konform)

### Phase 1: Modelle und Spezifikation
- **Task 1:** Diese Spezifikation finalisieren und als `spec-029-autonomous-overnight-agents.md` speichern.
- **Task 2:** Pydantic-Modelle für `Mission`, `TaskQueueItem` und `MissionResult` in `shared/models/night_watch.py` definieren.

### Phase 2: Kernfunktionalität
- **Task 3:** Tests für den `overnight_orchestrator` schreiben.
- **Task 4:** `scripts/overnight_orchestrator.py` implementieren.
- **Task 5:** Tests für den `overnight_worker` schreiben.
- **Task 6:** `scripts/overnight_worker.py` implementieren.

### Phase 3: Integration und Abschluss
- **Task 7:** Den Befehl `/start-overnight-agents` in `.claude/commands/` anlegen.
- **Task 8:** Eine erste `overnight_missions.json` mit den Missionen "Pydantic-Migration" und "API-Referenz generieren" erstellen.
- **Task 9:** Einen End-to-End-Integrationstest schreiben und durchführen.

## 6. Verfassungskonformität

- **Artikel III (Automatisierte Durchsetzung):** Dieser Prozess ist die Verkörperung von Artikel III, da er proaktiv und automatisiert Qualitätsstandards in der Codebase durchsetzt.
- **Artikel IV (Kontinuierliches Lernen):** Die "Nachtwache" ist ein System, das die Codebase kontinuierlich verbessert und somit das System als Ganzes "lernt" und weiterentwickelt.

## 7. Technische Details

### 7.1 Task Queue Format

```json
{
  "version": "1.0",
  "created_at": "2025-10-12T03:00:00Z",
  "mission_set": "full",
  "tasks": [
    {
      "id": "task_001",
      "title": "Pydantic Migration",
      "command": "/primeA 'Migrate all Dict[str, Any] to Pydantic models'",
      "priority": 1,
      "estimated_duration_minutes": 30,
      "status": "pending",
      "assigned_to": null,
      "branch_name": null,
      "started_at": null,
      "completed_at": null
    }
  ]
}
```

### 7.2 File Locking Strategy

- Use `fcntl.flock()` (Unix) for exclusive file locking
- Retry logic with exponential backoff (Article I compliance)
- Maximum lock hold time: 5 seconds
- Lock acquisition timeout: 30 seconds

### 7.3 Git Branch Naming Convention

Pattern: `night-watch/<mission-slug>-<timestamp>`

Examples:
- `night-watch/pydantic-migration-20251012-0315`
- `night-watch/api-docs-generation-20251012-0345`
- `night-watch/test-coverage-improvement-20251012-0420`

### 7.4 Worker Communication

- Status updates written to `task_queue.json` (atomic updates with locking)
- Progress logs written to `logs/overnight/<worker-id>-<timestamp>.log`
- Final summary aggregated by orchestrator from individual worker logs

### 7.5 Error Handling

- Worker failure: Mark task as `failed`, continue with next task
- Git conflict: Abort task, mark as `conflict`, log details
- Timeout: Kill worker process after 60 minutes per task
- Network error (for distributed workers): Retry 3x with exponential backoff

### 7.6 Success Criteria per Task

1. `/primeA` command exits with code 0
2. All tests pass (`python run_tests.py --run-all`)
3. Git status clean (no uncommitted changes)
4. Branch pushed to remote successfully

## 8. Future Enhancements (Post-MVP)

- **Distributed Coordination:** Use Redis/PostgreSQL instead of file-based queue for better scalability
- **Web Dashboard:** Real-time monitoring of worker progress
- **Slack/Discord Integration:** Send notifications when missions complete
- **Auto-PR Creation:** Automatically create PRs for completed branches
- **Smart Scheduling:** Use ML to predict task duration and optimize worker allocation
- **Cost Tracking:** Track API costs per mission for budget optimization
