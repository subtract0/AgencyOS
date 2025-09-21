# ADR-001: Vollständiger Kontext vor Aktion

## Status
**Accepted** - 2025-09-21

## Context
Während der Selbstheilungs-Mission (Phase 2) wurde ein kritisches Anti-Pattern identifiziert: Das voreilige Fortfahren bei Timeouts oder unvollständigen Test-Läufen führte zu:
- Fatalen Lücken im Kontext
- Stundenlanger Arbeit in Sackgassen
- Verletzung des "No Broken Windows" Prinzips
- Unvollständiger Selbstheilung trotz gegenteiliger Behauptung

## Decision
**Wir etablieren das Prinzip: "Vollständiger Kontext vor Aktion"**

### Konkrete Regeln:

1. **Timeout-Handling**
   - Bei JEDEM Timeout: Anhalten und analysieren
   - Mit längerem Zeitfenster wiederholen (2x, 3x, bis zu 10x)
   - Erst fortfahren, wenn das vollständige Bild vorliegt
   - NIEMALS sagen "ich habe genug gesehen" bei unvollständigen Daten

2. **Test-Ausführung**
   - ALLE Tests müssen bis zum Ende laufen
   - Bei Failures oder Skips: SOFORT anhalten
   - Fehlerhafte Tests ZUERST reparieren, bevor neue Features
   - Keine Mission ist abgeschlossen, solange Tests fehlschlagen

3. **Kontext-Verifikation**
   - Explizit prüfen: "Habe ich alle Informationen?"
   - Bei Unsicherheit: Nochmal ausführen
   - Lieber 5 Minuten länger warten als 5 Stunden in die falsche Richtung

4. **"No Broken Windows" gilt absolut**
   - Auch für generierten Code
   - Auch für "temporäre" Lösungen
   - Auch unter Zeitdruck

## Consequences

### Positive
- Keine fatalen Kontextlücken mehr
- Vermeidung von Sackgassen
- Höhere Code-Qualität
- Vertrauen in die Vollständigkeit der Analyse
- Zeit-Ersparnis durch Vermeidung von Nacharbeit

### Negative
- Initial längere Ausführungszeiten
- Mehr Ressourcenverbrauch für vollständige Läufe
- Gefühl von "Langsamkeit" bei der Arbeit

### Mitigation
- Timeout-Werte proaktiv anpassen (default: 2min → 5min für Tests)
- Parallele Ausführung wo möglich
- Klare Kommunikation über längere Wartezeiten

## Implementation

```python
# Beispiel: Test-Ausführung mit Retry-Logik
def run_tests_with_complete_context(test_path, max_retries=3):
    timeout = 120000  # Start mit 2 Minuten

    for attempt in range(max_retries):
        result = run_tests(test_path, timeout=timeout)

        if result.timed_out:
            print(f"Timeout nach {timeout/1000}s - Wiederhole mit längerem Timeout")
            timeout *= 2  # Verdoppeln für nächsten Versuch
            continue

        if result.incomplete:
            print("Unvollständige Ergebnisse - Wiederhole")
            continue

        # Vollständige Ergebnisse erhalten
        if result.failures > 0 or result.errors > 0:
            print(f"STOP: {result.failures} failures, {result.errors} errors")
            print("Diese MÜSSEN zuerst behoben werden")
            return False

        return True

    raise Exception("Konnte keine vollständigen Test-Ergebnisse erhalten")
```

## Lessons Learned
- Ein Timeout ist ein STOP-Signal, kein "weiter so"
- "Ich habe genug gesehen" ist fast immer falsch
- 10 Minuten warten spart 10 Stunden Debugging
- Vollständigkeit > Geschwindigkeit

## References
- Selbstheilungs-Mission Phase 2 (2025-09-21)
- "No Broken Windows" - The Pragmatic Programmer
- Test-Driven Development Best Practices

## Review
- Author: AgencyCodeAgent
- Reviewers: @am
- Date: 2025-09-21

---

*"Better to wait for complete truth than to act on partial lies."*