"""
Test Planner Agent behavior, specifically verifying that it asks clarifying questions
when requirements are unclear or incomplete.
"""

import os

import pytest
from agency_swarm import Agency
from dotenv import load_dotenv

from agency_code_agent.agency_code_agent import create_agency_code_agent
from planner_agent.planner_agent import create_planner_agent

# Load environment variables
load_dotenv()


@pytest.fixture(autouse=True)
def cleanup_fib():
    """Clean up fib.py after each test"""
    yield
    if os.path.exists("fib.py"):
        os.unlink("fib.py")


@pytest.fixture
def planner_agency():
    """Create agency with planner agent entry point for testing"""
    planner = create_planner_agent(model="gpt-5-mini", reasoning_effort="low")
    coder = create_agency_code_agent(model="gpt-5-mini", reasoning_effort="low")

    # Set up handoffs
    planner.handoffs = [coder]
    coder.handoffs = [planner]

    return Agency(
        planner,  # Planner is the entry point
        shared_instructions="Test agency for Planner Agent question-asking behavior validation.",
    )


@pytest.fixture
def ambiguous_queries():
    """Test queries that should trigger clarifying questions from the planner"""
    return [
        {
            "id": 1,
            "category": "Vague Feature Request",
            "query": "Add authentication to the app",
            "expected_questions": [
                "What type of authentication",
                "login method",
                "user registration",
                "session management",
                "which app",
            ],
        },
        {
            "id": 2,
            "category": "Missing Context",
            "query": "Fix the bug",
            "expected_questions": [
                "what bug",
                "which file",
                "error message",
                "symptoms",
                "reproduce",
            ],
        },
        {
            "id": 3,
            "category": "Incomplete Requirements",
            "query": "Create a database",
            "expected_questions": [
                "what type of database",
                "which data",
                "tables",
                "schema",
                "purpose",
            ],
        },
        {
            "id": 4,
            "category": "Ambiguous Scope",
            "query": "Optimize performance",
            "expected_questions": [
                "which part",
                "what type of performance",
                "metrics",
                "current issues",
                "target",
            ],
        },
    ]


@pytest.mark.asyncio
async def test_planner_asks_clarifying_questions_vague_auth(planner_agency):
    """Test that planner asks questions for vague authentication request"""
    query = "Add authentication to the app"
    run_result = await planner_agency.get_response(query)

    # Extract the actual response text from RunResult
    if hasattr(run_result, "final_output") and run_result.final_output:
        response = run_result.final_output
    elif hasattr(run_result, "text"):
        response = run_result.text
    else:
        response = str(run_result)

    # Should ask clarifying questions, not immediately start planning
    question_indicators = [
        "?",
        "clarify",
        "specific",
        "what type",
        "which",
        "how",
        "details",
        "requirements",
        "preferences",
        "constraints",
    ]

    has_questions = any(
        indicator.lower() in response.lower() for indicator in question_indicators
    )
    assert has_questions, (
        f"Response should ask clarifying questions. Got: {response[:500]}..."
    )

    # Should not immediately jump into detailed planning without asking questions first
    planning_indicators = [
        "step 1:",
        "first step",
        "implementation plan",
        "detailed breakdown",
    ]
    has_premature_planning = any(
        indicator.lower() in response.lower() for indicator in planning_indicators
    )

    # Allow planning if it comes after asking questions
    if has_premature_planning and has_questions:
        # If both planning and questions exist, make sure questions come first
        response_lower = response.lower()
        first_question = min(
            [
                response_lower.find(ind)
                for ind in question_indicators
                if ind in response_lower
            ]
        )
        first_planning = min(
            [
                response_lower.find(ind)
                for ind in planning_indicators
                if ind in response_lower
            ]
        )
        assert first_question < first_planning, "Questions should come before planning"
    elif has_premature_planning and not has_questions:
        assert False, "Should not start detailed planning without clarification"


@pytest.mark.asyncio
async def test_planner_asks_about_missing_context(planner_agency):
    """Test that planner asks for context when request lacks information"""
    query = "Fix the bug"
    run_result = await planner_agency.get_response(query)

    # Extract the actual response text from RunResult
    if hasattr(run_result, "final_output") and run_result.final_output:
        response = run_result.final_output
    elif hasattr(run_result, "text"):
        response = run_result.text
    else:
        response = str(run_result)

    # Should ask for specific information about the bug
    context_questions = [
        "what bug",
        "which bug",
        "error",
        "issue",
        "problem",
        "symptoms",
        "reproduce",
        "file",
        "code",
        "details",
    ]

    asks_context = any(q.lower() in response.lower() for q in context_questions)
    assert asks_context, f"Should ask for bug context. Got: {response[:500]}..."


@pytest.mark.asyncio
async def test_planner_asks_about_incomplete_requirements(planner_agency):
    """Test that planner asks for complete requirements"""
    query = "Create a database"
    run_result = await planner_agency.get_response(query)

    # Extract the actual response text from RunResult
    if hasattr(run_result, "final_output") and run_result.final_output:
        response = run_result.final_output
    elif hasattr(run_result, "text"):
        response = run_result.text
    else:
        response = str(run_result)

    # Should ask about database specifics
    requirement_questions = [
        "type",
        "data",
        "tables",
        "schema",
        "structure",
        "purpose",
        "requirements",
        "what kind",
        "which",
    ]

    asks_requirements = any(
        q.lower() in response.lower() for q in requirement_questions
    )
    assert asks_requirements, (
        f"Should ask for database requirements. Got: {response[:500]}..."
    )


@pytest.mark.asyncio
async def test_planner_comprehensive_question_behavior(
    planner_agency, ambiguous_queries
):
    """Test planner's question-asking behavior across multiple ambiguous queries"""
    results = []

    for test_case in ambiguous_queries:
        try:
            run_result = await planner_agency.get_response(test_case["query"])

            # Extract the actual response text from RunResult
            if hasattr(run_result, "final_output") and run_result.final_output:
                response = run_result.final_output
            elif hasattr(run_result, "text"):
                response = run_result.text
            else:
                response = str(run_result)

            # Check if response contains question marks or clarifying language
            has_questions = "?" in response
            has_clarifying_language = any(
                phrase.lower() in response.lower()
                for phrase in [
                    "clarify",
                    "specific",
                    "details",
                    "requirements",
                    "what",
                    "which",
                    "how",
                ]
            )

            # Check if it asks for any expected information
            asks_expected = any(
                expected.lower() in response.lower()
                for expected in test_case["expected_questions"]
            )

            asks_questions = has_questions or has_clarifying_language or asks_expected

            result = {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "query": test_case["query"],
                "asks_questions": asks_questions,
                "response_preview": response[:300] + "..."
                if len(response) > 300
                else response,
            }
            results.append(result)

        except Exception as e:
            results.append(
                {
                    "test_id": test_case["id"],
                    "category": test_case["category"],
                    "query": test_case["query"],
                    "asks_questions": False,
                    "response_preview": f"ERROR: {str(e)}",
                }
            )

    # Assert that planner asks questions for most ambiguous queries
    questioning_behavior = sum(1 for r in results if r["asks_questions"])
    total_tests = len(results)

    assert questioning_behavior >= (total_tests * 0.75), (
        f"Planner should ask questions for at least 75% of ambiguous queries. "
        f"Got {questioning_behavior}/{total_tests} questioning responses."
    )

    return results


@pytest.mark.asyncio
async def test_planner_with_clear_requirements_minimal_questions(planner_agency):
    """Test that planner doesn't over-question when requirements are clear"""
    clear_query = (
        "Create a Python function called 'fibonacci' that takes an integer n as input "
        "and returns the nth Fibonacci number using iteration (not recursion). "
        "The function should handle edge cases for n <= 0 and should be saved to a file called 'fib.py'. "
        "Include proper error handling and docstring documentation."
    )

    run_result = await planner_agency.get_response(clear_query)

    # Extract the actual response text from RunResult
    if hasattr(run_result, "final_output") and run_result.final_output:
        response = run_result.final_output
    elif hasattr(run_result, "text"):
        response = run_result.text
    else:
        response = str(run_result)

    # Should not ask excessive clarifying questions for clear requirements
    question_count = response.count("?")
    excessive_questions = question_count > 2  # Allow some follow-up but not excessive

    assert not excessive_questions, (
        f"Should not ask excessive questions for clear requirements. "
        f"Found {question_count} questions in response."
    )
