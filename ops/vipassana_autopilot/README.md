# Vipassana Autopilot: AgencyOS Completion Engine v0

This folder is a launch package for running AgencyOS productively during Alex's unattended 10-day+ window.

The system is designed as a **continuous autonomous Kanban worker pool** governed periodically by a **GPT-5.5 Hermes fleet governor**.

Workers should not wait for Hermes to hand them every task. Workers continuously claim bounded tasks from the pool, execute them, validate outputs, write append-only evidence, and claim the next eligible task. Hermes periodically