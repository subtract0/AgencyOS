
from cells.maintenance.refactor_agent import RefactorAgent

def run_scan():
    agent = RefactorAgent()
    print("running scan...")
    report = agent.scan()
    with open("CODE_HEALTH_REPORT.md", "w") as f:
        f.write("# Code Health Report\n\n")
        f.write(report)
    print("Report generated.")

if __name__ == "__main__":
    run_scan()
