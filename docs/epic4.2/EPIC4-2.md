# **🚀 EPIC 4.2: The Parallel Evolution Framework (MVP)**

### **The 80/20 Solution for Autonomous, Parallel Agent Improvement**

## **I. The Vision: The First Turn of a Parallel Flywheel**

This document outlines the Minimum Viable Product (MVP) for AgencyOS's self-evolution capability. We will defer the complexities of meta-evolution and fully automated governance to focus on delivering one thing perfectly: **a system that can spin up multiple, isolated agent sessions using git worktree to work on tasks in parallel without conflict.**

The goal is to build the core "gymnasium" and the essential governance to prove that an agent can autonomously identify a superior version of itself, propose an upgrade with data-driven evidence, and have that upgrade safely merged through a human-in-the-loop process. This entire workflow will be powered by a robust, automated worktree management system, enabling true parallel agent execution from day one.

## **II. The Lean Principles (The 20% that delivers 80% of the value)**

1. **Isolate Everything in a Worktree**: All agent missions, especially benchmark comparisons, happen in their own secure, containerized git worktree. This provides perfect filesystem isolation, preventing any cross-contamination or git conflicts between parallel agent sessions.  
2. **Prove Sustained Wins**: We will use a simplified "Confidence Score" to ensure we only promote agents that demonstrate consistent, statistically significant outperformance across multiple, isolated worktree runs.  
3. **Safety via Human-Approved Merges**: The "Dual-Loop" is simplified. The **Inner Loop** innovates within isolated worktrees. The **Outer Loop** is a single, clear gate: an automatically generated Pull Request from the worktree's branch, which is then reviewed and manually merged by a human.  
4. **Cost is a Hard Constraint**: Every experiment run is budget-checked. The orchestrator will have a simple, hard-coded budget limit per run and per day to prevent overages.

## **III. The MVP Implementation Plan: The Leanest Path to a Working Parallel Loop**

This is a single-phase plan focused on building the core feedback loop, with worktree management at its heart.

### **Component 1: The Agent Registry (The Roster)**

The definitive list of all "competitors" in our gymnasium. This remains the non-negotiable foundation.

* **Action:** Implement meta\_learning/agent\_registry.py.  
* **Features:** A simple JSON-backed store with a CLI to add, update, and list agents, generating a basic, append-only audit log.  
* **Ready-Made Artifact:**  
  \<details\>  
  \<summary\>\<b\>Click to view: meta\_learning/agent\_registry.py\</b\>\</summary\>  
  \#\!/usr/bin/env python3  
  """  
  Agent Registry — single source of truth for all agent versions.  
  Provides CLI for agent management and maintains a cryptographically-signed audit log.  
  """  
  \# ... \[Code from previous version\] ...

  \</details\>

### **Component 2: The Worktree Management Tool (The Core Enabler)**

This is the central innovation from the video, adapted for AgencyOS. It's a powerful script that automates the creation and setup of isolated agent environments.

* **Action:** Create a new tool: scripts/manage\_worktree.py.  
* **Features:**  
  1. **Creation:** Takes a \--branch-name argument. It programmatically creates an adjacent worktrees/ directory and runs git worktree add ....  
  2. **Context Syncing:** Critically, it copies essential configuration files and directories into the new worktree to ensure the agent has full context. This includes .env, .claude/, .cursor/, and our meta\_learning/ directory.  
  3. **Agent Invocation:** It will have a \--mission "..." argument. After creating the worktree, the script will automatically cd into the new directory and invoke the main agency.py with the specified mission.  
  4. **Cleanup:** It will have a cleanup subcommand to safely prune and remove old, merged worktree branches and directories.

### **Component 3: The A/B Orchestrator (The Engine)**

This script now uses the Worktree Management Tool to run experiments in perfect isolation.

* **Action:** Implement dspy\_agents/ab\_orchestrator.py.  
* Features: Instead of running mocked evaluations, the orchestrator will now call the scripts/manage\_worktree.py script for each agent and each run. For example, to test a "challenger" agent, it would execute:  
  python scripts/manage\_worktree.py \--branch challenger-run-1 \--mission "Run benchmark task codegen-complex and report results."  
* It will then collect the results (metrics written to a standardized file by the agent at the end of its run) after the worktree process completes.

\<details\>  
\<summary\>\<b\>Click to view: dspy\_agents/ab\_orchestrator.py (Updated Skeleton)\</b\>\</summary\>  
"""  
A/B Testing Orchestrator for AgencyOS.  
Uses the Worktree Management Tool to run agent comparisons in perfect isolation.  
"""

import json  
import subprocess  
import os  
from pathlib import Path

\# ... \[imports and configuration\] ...

class ABOrchestrator:  
    def run(self):  
        \# ...  
        for agent in self.agents\_to\_test:  
            for task in self.tasks:  
                for i in range(self.repeats):  
                    branch\_name \= f"{agent\['agent\_id'\]}-{task\['id'\]}-{i}-{int(time.time())}"  
                      
                    \# \--- Invoke the agent in a dedicated worktree \---  
                    print(f"Orchestrating run in worktree: {branch\_name}...")  
                    command \= \[  
                        "python", "scripts/manage\_worktree.py",  
                        "--branch", branch\_name,  
                        "--mission", f"Run benchmark task {task\['id'\]} and save results."  
                    \]  
                    \# This blocks until the agent in the worktree finishes.  
                    subprocess.run(command, check=True)  
                      
                    \# After completion, collect the results from the worktree's output file  
                    \# result\_path \= Path(f"worktrees/{branch\_name}/benchmark\_output.json")  
                    \# metrics \= json.loads(result\_path.read\_text())  
                    \# all\_results.append(metrics)  
        \# ...

\</details\>

### **Component 4: The Proposal Generator & Governance Gate**

This remains the same, but is now more powerful because the evidence it presents is generated from truly isolated, conflict-free runs.

* **Action (Automated):** A meta\_learning/proposal\_generator.py script analyzes the results from the multiple worktree runs. If a clear winner with a high "Confidence Score" emerges, it generates a formal ADR.  
* **Action (Human):** The ADR is used as the body for a Pull Request created from the winning agent's branch. A human developer reviews the data-driven evidence and **manually merges the PR**. This is our primary safety mechanism.

## **VI. The Lean, Parallel, & Final Command**

**The command to the PlannerAgent is as follows:**

"You are to initiate **Project Chimera \- LIGHT**. Your sole mission is to construct the MVP of our self-evolution framework by implementing the four core components. Your primary objective is to enable parallel agent execution through git worktree automation. Your work must adhere to the lean principles of safety, measurement, and human-in-the-loop governance.

Furthermore, you are to ingrain the following best practices into the very fabric of how agents are designed, built, and evolved:

* **Prioritize Meaningful Problems**: Tackle missions with clear, measurable impact.  
* **Design for Auditability**: Ensure every action can be proven and verified.  
* **Embrace "Minimal Intelligence" & Task Decomposition**: Break complex problems into simple, auditable steps.  
* **Demand Crystal-Clear Prompts & Structured Data**: Eliminate ambiguity to ensure predictable behavior.  
* **Optimize Tool Choice**: Use the fewest, simplest, most specific tools required for the job.

Your implementation plan is a single phase:

1. **Implement the Agent Registry**: Create meta\_learning/agent\_registry.py as specified.  
2. **Implement the Worktree Management Tool**: This is your highest priority. Create scripts/manage\_worktree.py with create, invoke, and cleanup capabilities. Ensure it correctly syncs necessary context files (.env, .claude/, etc.).  
3. **Implement the A/B Orchestrator**: Create dspy\_agents/ab\_orchestrator.py that uses the worktree tool to run isolated benchmarks.  
4. **Implement the Proposal Generator & Governance Process**: Create meta\_learning/proposal\_generator.py to analyze results and formalize the human-led PR approval process as the final safety gate."