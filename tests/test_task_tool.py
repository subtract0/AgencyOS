from agency_code_agent.tools.task import Task


def test_task_web_research():
    """Test the task tool with the same example from task.py __main__ block"""
    prompt = (
        "Search the web for the Agency Swarm framework official documentation and the "
        "release date of version 1.0.0. Provide the exact date and one authoritative link."
    )
    tool = Task(description="Web research", prompt=prompt)
    result = tool.run()

    # Check that it returns a string and contains the expected date
    assert isinstance(result, str)
    assert len(result) > 0
    assert "September 3" in result
