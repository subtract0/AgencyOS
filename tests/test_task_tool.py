import pytest
from agency_code_agent.tools.task import Task


def test_task_search_functionality():
    """Test task tool with search-related prompts"""
    tool = Task(
        description="Find files",
        prompt="Search for all Python files containing 'import requests' in the project"
    )
    result = tool.run()
    
    assert "Task 'Find files' initiated" in result
    assert "Searching with prompt" in result
    assert "import requests" in result
    assert "simulated agent response" in result


def test_task_find_functionality():
    """Test task tool with find-related prompts"""
    tool = Task(
        description="Locate config",
        prompt="Find configuration files in the system that contain database settings"
    )
    result = tool.run()
    
    assert "Task 'Locate config' initiated" in result
    assert "Searching with prompt" in result
    assert "database settings" in result


def test_task_analyze_functionality():
    """Test task tool with analysis prompts"""
    tool = Task(
        description="Code analysis",
        prompt="Analyze the authentication system to understand how user sessions are managed"
    )
    result = tool.run()
    
    assert "Task 'Code analysis' initiated" in result
    assert "Analyzing with prompt" in result
    assert "authentication system" in result
    assert "simulated agent response" in result


def test_task_understand_functionality():
    """Test task tool with understanding prompts"""
    tool = Task(
        description="Study codebase",
        prompt="Understand how the payment processing module integrates with external APIs"
    )
    result = tool.run()
    
    assert "Task 'Study codebase' initiated" in result
    assert "Analyzing with prompt" in result
    assert "payment processing" in result


def test_task_general_functionality():
    """Test task tool with general prompts"""
    tool = Task(
        description="Review code",
        prompt="Check the error handling patterns used throughout the application"
    )
    result = tool.run()
    
    assert "Task 'Review code' initiated" in result
    assert "error handling patterns" in result
    assert "simulated agent response" in result


def test_task_complex_search_query():
    """Test task with complex search requirements"""
    tool = Task(
        description="Multi-step search",
        prompt="Search for all logging configurations and find which files use structured logging vs simple print statements"
    )
    result = tool.run()
    
    assert "Task 'Multi-step search' initiated" in result
    assert "logging configurations" in result
    assert "structured logging" in result


def test_task_analysis_with_requirements():
    """Test task with detailed analysis requirements"""
    tool = Task(
        description="Security review",
        prompt="Analyze the codebase for potential security vulnerabilities, focusing on input validation and SQL injection risks"
    )
    result = tool.run()
    
    assert "Task 'Security review' initiated" in result
    assert "security vulnerabilities" in result
    assert "input validation" in result


def test_task_short_description():
    """Test task with very short description"""
    tool = Task(
        description="Quick search",
        prompt="Find all TODO comments in the codebase"
    )
    result = tool.run()
    
    assert "Task 'Quick search' initiated" in result
    assert "TODO comments" in result


def test_task_long_description():
    """Test task with longer description"""
    tool = Task(
        description="Comprehensive database analysis",
        prompt="Perform a comprehensive analysis of all database-related code including models, migrations, queries, and connection handling"
    )
    result = tool.run()
    
    assert "Task 'Comprehensive database analysis' initiated" in result
    assert "database-related code" in result
    assert "migrations" in result


def test_task_case_insensitive_keywords():
    """Test that keyword detection is case insensitive"""
    # Test uppercase SEARCH
    tool1 = Task(
        description="SEARCH files",
        prompt="SEARCH for all configuration files"
    )
    result1 = tool1.run()
    assert "Searching with prompt" in result1
    
    # Test mixed case Find
    tool2 = Task(
        description="Find items",
        prompt="Find all instances of deprecated functions"
    )
    result2 = tool2.run()
    assert "Searching with prompt" in result2
    
    # Test uppercase ANALYZE
    tool3 = Task(
        description="Code review",
        prompt="ANALYZE the performance bottlenecks"
    )
    result3 = tool3.run()
    assert "Analyzing with prompt" in result3


def test_task_multiple_keywords():
    """Test task with multiple keywords in prompt"""
    tool = Task(
        description="Complex task",
        prompt="Search for authentication code and then analyze how it integrates with the user management system"
    )
    result = tool.run()
    
    # Should trigger search functionality (first matching keyword)
    assert "Searching with prompt" in result
    assert "authentication code" in result


def test_task_no_matching_keywords():
    """Test task that doesn't match search/find/analyze/understand keywords"""
    tool = Task(
        description="Generic task",
        prompt="Review the documentation and update the changelog with recent changes"
    )
    result = tool.run()
    
    assert "Task 'Generic task' initiated" in result
    assert "documentation" in result
    assert "changelog" in result
    # Should use general task handling
    assert "simulated agent response" in result


def test_task_error_handling():
    """Test task error handling with edge cases"""
    # Test with empty description (should still work due to Field validation)
    try:
        tool = Task(description="", prompt="Test prompt")
        result = tool.run()
        assert isinstance(result, str)
    except Exception as e:
        # Pydantic validation might prevent empty description
        assert "description" in str(e).lower() or "field required" in str(e).lower()
    
    # Test with empty prompt
    try:
        tool = Task(description="Test", prompt="")
        result = tool.run()
        assert isinstance(result, str)
    except Exception as e:
        # Pydantic validation might prevent empty prompt
        assert "prompt" in str(e).lower() or "field required" in str(e).lower()


def test_task_special_characters():
    """Test task with special characters in description and prompt"""
    tool = Task(
        description="Search & Find",
        prompt="Find all files with names containing special chars: @#$%^&*(){}[]"
    )
    result = tool.run()
    
    assert "Task 'Search & Find' initiated" in result
    assert "special chars" in result
    assert "@#$%^&*()" in result


def test_task_long_prompt():
    """Test task with very long prompt"""
    long_prompt = """
    This is a very comprehensive task that requires searching through multiple directories 
    and analyzing various types of files including Python scripts, configuration files, 
    documentation, test files, and deployment scripts. The goal is to understand the 
    complete architecture of the system, identify potential improvements, find security 
    issues, check for code quality problems, analyze performance bottlenecks, and create 
    a detailed report with actionable recommendations for the development team.
    """
    
    tool = Task(
        description="Full analysis",
        prompt=long_prompt
    )
    result = tool.run()
    
    assert "Task 'Full analysis' initiated" in result
    assert "comprehensive task" in result


def test_task_programming_languages():
    """Test task mentioning various programming languages"""
    tool = Task(
        description="Multi-lang search",
        prompt="Search for files written in Python, JavaScript, TypeScript, Go, and Rust to find common patterns"
    )
    result = tool.run()
    
    assert "Multi-lang search" in result
    assert "Python" in result
    assert "JavaScript" in result
    assert "common patterns" in result


def test_task_technical_analysis():
    """Test task with technical analysis requirements"""
    tool = Task(
        description="Architecture review",
        prompt="Analyze the microservices architecture to understand service boundaries, communication patterns, and data flow"
    )
    result = tool.run()
    
    assert "Architecture review" in result
    assert "microservices" in result
    assert "service boundaries" in result
    assert "Analyzing with prompt" in result


def test_task_debugging_scenario():
    """Test task for debugging scenarios"""
    tool = Task(
        description="Debug issue",
        prompt="Find all error handling code and analyze why exceptions are not being caught properly in the payment module"
    )
    result = tool.run()
    
    assert "Debug issue" in result
    assert "error handling" in result
    assert "payment module" in result


def test_task_refactoring_scenario():
    """Test task for refactoring scenarios"""
    tool = Task(
        description="Refactor prep",
        prompt="Search for all duplicate code patterns and understand which functions could be extracted into reusable utilities"
    )
    result = tool.run()
    
    assert "Refactor prep" in result
    assert "duplicate code" in result
    assert "reusable utilities" in result
    assert "Searching with prompt" in result
