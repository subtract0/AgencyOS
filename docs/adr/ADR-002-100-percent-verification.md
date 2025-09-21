# ADR-002: 100% Verifikation und Stabilität

## Status
**Accepted** - 2025-09-21

## Context
Nach der Selbstheilungs-Mission (Phase 2) mit 98.6% Test-Erfolgsrate wurde klar: "Fast fertig" ist nicht fertig. Die verbleibenden 1.4% fehlerhaften Tests sind nicht akzeptabel. "No Broken Windows" toleriert keine einzige zerbrochene Scheibe.

## Decision
**Eine Aufgabe ist erst dann fertig, wenn sie zu 100% verifiziert und stabil ist.**

### Konkrete Regeln:

1. **100% Test-Erfolgsrate ist nicht verhandelbar**
   - Der main-Branch MUSS immer 100% Tests bestehen
   - Kein Merge ohne vollständig grüne CI-Pipeline
   - Fehlschlagende Tests blockieren ALLES andere

2. **Keine Hacks oder Workarounds**
   - Tests müssen ECHTE Funktionalität verifizieren
   - Keine Tests deaktivieren oder "skip" markieren (außer platform-spezifisch)
   - Keine Assertions entfernen, um Tests zum Laufen zu bringen
   - Wenn ein Test fehlschlägt, ist der CODE falsch, nicht der Test

3. **"Lösche zuerst das Feuer"**
   - BEVOR neue Features: Alle Tests müssen grün sein
   - BEVOR Refactoring: Alle Tests müssen grün sein
   - BEVOR Optimierung: Alle Tests müssen grün sein
   - Broken Windows haben IMMER höchste Priorität

4. **Test-Driven Development**
   - Neue Features MÜSSEN mit Tests kommen
   - Tests werden MIT dem Code eingecheckt, nicht später
   - Ohne Tests keine Feature-Completion

5. **Definition of Done**
   - Code geschrieben ✓
   - Tests geschrieben ✓
   - Alle Tests bestehen ✓
   - Code Review ✓
   - CI Pipeline grün ✓
   - = FERTIG (nicht vorher!)

## Consequences

### Positive
- Absolute Vertrauenswürdigkeit des Codes
- Keine versteckten Bugs
- Keine technische Schuld
- Schnellere Entwicklung langfristig
- Stolz auf die Codebasis

### Negative
- Initial langsamer
- Kein "quick and dirty"
- Mehr Aufwand bei Prototypen
- Frustration bei hartnäckigen Tests

### Mitigation
- Test-Fehler sofort beheben, nicht aufschieben
- Pair Programming bei schwierigen Tests
- Test-Infrastruktur kontinuierlich verbessern
- Klare Fehlermeldungen in Tests

## Implementation Example

```python
# FALSCH - Test "angepasst" um zu bestehen
def test_feature():
    result = my_function()
    # assert result == expected  # Auskommentiert weil es fehlschlägt
    assert result is not None  # Schwächere Assertion damit es grün wird

# RICHTIG - Problem im Code beheben
def test_feature():
    result = my_function()
    assert result == expected  # Test bleibt stark, Code wird gefixt
```

## Enforcement
```bash
# Pre-commit Hook
#!/bin/bash
pytest tests/ --tb=no -q
if [ $? -ne 0 ]; then
    echo "❌ Tests fehlgeschlagen. Commit blockiert."
    echo "Regel: 100% Tests müssen bestehen (ADR-002)"
    exit 1
fi

# GitHub Actions
- name: Enforce 100% Test Success
  run: |
    pytest tests/
    if [ $? -ne 0 ]; then
      echo "::error::ADR-002 verletzt: Tests müssen zu 100% bestehen"
      exit 1
    fi
```

## Metrics
- Test-Erfolgsrate: MUSS 100% sein
- Test-Coverage: SOLL >80% sein
- Neue Features ohne Tests: 0
- Zeit bis zur Test-Reparatur: <24h

## References
- ADR-001: Vollständiger Kontext vor Aktion
- "No Broken Windows" - The Pragmatic Programmer
- Test-Driven Development - Kent Beck

## Review
- Author: AgencyCodeAgent
- Mandated by: @am
- Date: 2025-09-21

---

*"Code without 100% passing tests is broken code in disguise."*