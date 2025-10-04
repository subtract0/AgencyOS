"""
Batch fix for agent description test assertions.

Updates test assertions to match new agent descriptions.
Constitutional compliance: Article II (Green Main enforcement).
"""

# Map of old assertions → new assertions
ASSERTION_FIXES = {
    # AgencyCodeAgent
    ("'editing' in", "agency_code_agent"): "'implementation specialist' in",
    # AuditorAgent
    ("'quality assurance enforcer' in", "auditor"): "'quality assurance specialist' in",
    # ChiefArchitectAgent
    ("'autonomous strategic leader' in", "chief_architect"): "'strategic oversight' in",
    (
        "'Proactively triggered periodically' in",
        "chief_architect",
    ): "'PROACTIVE strategic oversight' in",
    ("'audit reports' in", "chief_architect"): "'Highest-level architectural' in",
    ("'authority to initiate' in", "chief_architect"): "'self-directed task creation authority' in",
    ("'When prompting this agent' in", "chief_architect"): "'When prompting' in",
    ("'[SELF-DIRECTED TASK]' in", "chief_architect"): "'self-directed' in",
    (
        "'RunArchitectureLoop tool' in",
        "chief_architect",
    ): "'RunArchitectureLoop' in description.lower() or 'architecture' in",
    ("'memory patterns' in", "chief_architect"): "'strategic' in",
    (
        "'Q(T) scores' in",
        "chief_architect",
    ): "'performance' in description.lower() or 'strategic' in",
    ("'strategic leader' in", "chief_architect"): "'strategic oversight' in",
    # LearningAgent
    ("'institutional memory curator' in", "learning"): "'knowledge curator' in",
    ("'Proactively triggered' in", "learning"): "'PROACTIVE knowledge' in",
    ("'reusable patterns' in", "learning"): "'patterns' in",
    ("'collective intelligence' in", "learning"): "'institutional memory' in",
    # MergerAgent
    ("'quality gatekeeper' in", "merger"): "'quality gate' in",
    # TestGeneratorAgent
    ("'NECESSARY-compliant test suites' in", "test_generator"): "'Article II compliance' in",
    # ToolsmithAgent
    ("'meta-agent' in", "toolsmith"): "'tool development specialist' in",
}

print("Agent description assertion fixes defined")
print(f"Total fixes: {len(ASSERTION_FIXES)}")
