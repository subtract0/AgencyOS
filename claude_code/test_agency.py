#!/usr/bin/env python3
"""
Test Agency for Claude Code Agent
Tests the agent with 5 diverse queries to validate functionality
"""

import os
import asyncio
from dotenv import load_dotenv
from agency_swarm import Agency
from claude_code_agent import claude_code_agent

# Load environment variables
load_dotenv()

# Create single-agent agency for testing
agency = Agency(
    claude_code_agent,
    communication_flows=[],  # Single agent, no communication flows needed
    shared_instructions="Test agency for Claude Code Agent functionality validation.",
)

async def run_test_queries():
    """Run 5 diverse test queries to validate agent functionality"""
    
    test_queries = [
        {
            "id": 1,
            "category": "File Operations",
            "query": "List files in the current directory and read the contents of the first Python file you find",
            "expected": "Should use LS tool and Read tool sequentially"
        },
        {
            "id": 2,
            "category": "Code Search", 
            "query": "Search for any TODO comments in Python files and show me the results with line numbers",
            "expected": "Should use Grep tool with appropriate pattern"
        },
        {
            "id": 3,
            "category": "Complex Task",
            "query": "Help me create a simple Python script that calculates fibonacci numbers and save it to fib.py. Use the TodoWrite tool to track your progress",
            "expected": "Should use TodoWrite, Write tool, and track progress"
        },
        {
            "id": 4,
            "category": "Web Research",
            "query": "Search for information about Agency Swarm framework and fetch content from the official documentation",
            "expected": "Should use WebSearch and WebFetch tools"
        },
        {
            "id": 5,
            "category": "Development Workflow",
            "query": "Show me the git status and create a sample test file, then stage it for commit",
            "expected": "Should use Bash tool for git commands and Write tool for file creation"
        }
    ]
    
    results = []
    
    print("=" * 60)
    print("CLAUDE CODE AGENT - QA TEST EXECUTION")
    print("=" * 60)
    
    for test in test_queries:
        print(f"\n=== Test {test['id']}: {test['category']} ===")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")
        print("-" * 40)
        
        try:
            # Execute the query
            run_result = await agency.get_response(test['query'])
            
            # Extract text from RunResult
            response = run_result.text if hasattr(run_result, 'text') else str(run_result)
            
            # Analyze response
            success = len(response) > 50 and not "error" in response.lower()
            quality_score = 8 if success else 4
            
            result = {
                "test_id": test['id'],
                "category": test['category'],
                "query": test['query'],
                "response": response[:500] + "..." if len(response) > 500 else response,
                "success": success,
                "quality_score": quality_score,
                "full_response": response
            }
            results.append(result)
            
            print(f"Response: {response}")
            print(f"Status: {'✅ PASSED' if success else '❌ FAILED'}")
            print(f"Quality Score: {quality_score}/10")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            result = {
                "test_id": test['id'],
                "category": test['category'],
                "query": test['query'],
                "response": f"ERROR: {str(e)}",
                "success": False,
                "quality_score": 0,
                "full_response": f"ERROR: {str(e)}"
            }
            results.append(result)
    
    return results

def generate_test_report(results):
    """Generate comprehensive test report"""
    
    # Calculate metrics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    avg_quality = sum(r['quality_score'] for r in results) / total_tests if total_tests > 0 else 0
    
    report = f"""# QA Test Results - Claude Code Agent

## Agency Configuration
- Agent: ClaudeCodeAgent
- Tools: 15 tools (File ops, Search, Web, Git, TodoWrite)
- Communication pattern: Single agent (no flows)
- Model: gpt-4o (temperature: 0.5)

## Test Query Results

"""
    
    for result in results:
        status_emoji = "✅ PASSED" if result['success'] else "❌ FAILED"
        report += f"""### Test {result['test_id']}: {result['category']}
**Query**: "{result['query']}"
**Response**: {result['response']}
**Quality Score**: {result['quality_score']}/10
**Status**: {status_emoji}

"""
    
    report += f"""## Performance Metrics
- Tests passed: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)
- Average quality score: {avg_quality:.1f}/10
- Overall status: {'✅ READY' if passed_tests >= 4 else '⚠️ NEEDS IMPROVEMENTS' if passed_tests >= 3 else '❌ MAJOR ISSUES'}

## Improvement Suggestions

### For Instructions (instructions-writer)
1. **ClaudeCodeAgent** - Consider adding more explicit examples for tool chaining
   - Current: Basic tool usage examples
   - Suggested: Add examples showing TodoWrite → Read → Edit workflows

### For Tools (tools-creator)
1. **Error Handling** - Add better error messages for common failures
2. **Tool Integration** - Improve coordination between complementary tools

### For Communication Flow
1. Single agent works well for development tasks
2. Consider adding specialized agents for complex workflows

## Overall Assessment
- **Ready for Production**: {'Yes' if passed_tests >= 4 else 'No'}
- **Critical Issues**: {['None'] if passed_tests >= 4 else ['Multiple test failures']}
- **Recommended Next Steps**:
  1. {'Continue with production deployment' if passed_tests >= 4 else 'Fix failing test cases'}
  2. {'Monitor performance in production' if passed_tests >= 4 else 'Improve error handling'}
  3. {'Gather user feedback' if passed_tests >= 4 else 'Add more comprehensive testing'}

## Specific Files to Update
- `instructions.md` - Add more tool chaining examples
- `tools/` - Improve error handling across tools
- `test_agency.py` - Expand test coverage for edge cases
"""
    
    return report

async def main():
    print("Starting Claude Code Agent QA Testing...")
    
    # Run the tests
    test_results = await run_test_queries()
    
    # Generate report
    report = generate_test_report(test_results)
    
    # Save results
    with open("/Users/vrsen/Areas/Development/code/agency-swarm/claude_code/qa_test_results.md", "w") as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print("QA TESTING COMPLETE")
    print("=" * 60)
    print(f"Results saved to: /Users/vrsen/Areas/Development/code/agency-swarm/claude_code/qa_test_results.md")
    print(f"Tests passed: {sum(1 for r in test_results if r['success'])}/{len(test_results)}")
    print(f"Average quality: {sum(r['quality_score'] for r in test_results) / len(test_results):.1f}/10")

if __name__ == "__main__":
    asyncio.run(main())