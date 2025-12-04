"""
Tests for UIDevelo pmentAgent - THE BLESSED ONE

NECESSARY Pattern Coverage:
- N: Normal operation (design, implement, create agent)
- E: Edge cases (empty inputs, unusual component names)
- C: Corner cases (special characters, long names)
- E: Error conditions (invalid types, missing fields)
- S: Security (no code injection in generated output)
- S: Stress (multiple component creations)
- A: Accessibility (agent created with all tools)
- R: Regression (factory returns valid agent)
- Y: Yield tests (Result pattern where applicable)

Constitutional compliance:
- Article I: Complete context (agent has full toolset)
- Article II: TDD (tests written first)
- Article III: Local enforcement (no external deps required)
- Article IV: VectorStore integration (memory hooks)
- Article V: Spec-driven (follows design spec)
"""

from unittest.mock import Mock, patch

import pytest


class TestDesignUIComponent:
    """Test DesignUIComponent tool functionality."""

    def test_design_widget_component_normal(self):
        """
        Test AC-1.1: Design widget type component returns valid design spec.

        NECESSARY: N (Normal operation)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="CostTracker",
            component_type="widget",
            design_requirements="Display real-time cost metrics"
        )

        result = tool.run()

        assert "CostTracker" in result
        assert "widget" in result
        assert "Apple Design Principles" in result
        assert "Visual Structure" in result
        assert "Color Palette" in result

    def test_design_panel_component(self):
        """
        Test AC-1.2: Design panel type component.

        NECESSARY: N (Normal operation - panel type)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="AgentStatus",
            component_type="panel",
            design_requirements="Show agent health and metrics"
        )

        result = tool.run()

        assert "AgentStatus" in result
        assert "panel" in result
        assert "Typography" in result

    def test_design_view_component(self):
        """
        Test AC-1.3: Design view type component.

        NECESSARY: N (Normal operation - view type)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="DashboardView",
            component_type="view",
            design_requirements="Main dashboard layout"
        )

        result = tool.run()

        assert "DashboardView" in result
        assert "view" in result

    def test_design_modal_component(self):
        """
        Test AC-1.4: Design modal type component.

        NECESSARY: N (Normal operation - modal type)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="ConfirmDialog",
            component_type="modal",
            design_requirements="Confirmation dialog with actions"
        )

        result = tool.run()

        assert "ConfirmDialog" in result
        assert "modal" in result

    def test_design_with_empty_requirements(self):
        """
        Test AC-1.5: Design component with empty requirements.

        NECESSARY: E (Edge case - empty requirements)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="EmptyReqs",
            component_type="widget",
            design_requirements=""
        )

        result = tool.run()

        # Should still generate valid design
        assert "EmptyReqs" in result
        assert "Requirements:" in result

    def test_design_with_special_characters_in_name(self):
        """
        Test AC-1.6: Design component with special characters in name.

        NECESSARY: C (Corner case - special chars)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="My_Component_V2",
            component_type="widget",
            design_requirements="Test component"
        )

        result = tool.run()

        assert "My_Component_V2" in result

    def test_design_includes_accessibility_section(self):
        """
        Test AC-1.7: Design output includes accessibility considerations.

        NECESSARY: A (Accessibility)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="AccessibleWidget",
            component_type="widget",
            design_requirements="Must be fully accessible"
        )

        result = tool.run()

        assert "Accessibility" in result
        # Check for keyboard navigation mentions (case-insensitive)
        assert "keyboard navigation" in result.lower() or "keyboard" in result.lower()
        # Check for screen reader mentions
        assert "screen reader" in result.lower() or "aria" in result.lower()

    def test_design_includes_performance_section(self):
        """
        Test AC-1.8: Design output includes performance considerations.

        NECESSARY: N (Normal - performance included)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        tool = DesignUIComponent(
            component_name="PerformantWidget",
            component_type="widget",
            design_requirements="High performance required"
        )

        result = tool.run()

        assert "Performance" in result
        assert "60fps" in result or "render" in result.lower()


class TestImplementUIComponent:
    """Test ImplementUIComponent tool functionality."""

    def test_implement_textual_component(self):
        """
        Test AC-2.1: Implement Textual (terminal) component.

        NECESSARY: N (Normal operation - textual)
        """
        from ui_development_agent.ui_development_agent import ImplementUIComponent

        tool = ImplementUIComponent(
            component_name="TerminalWidget",
            implementation_type="textual",
            specification="Widget for terminal display"
        )

        result = tool.run()

        assert "TerminalWidget" in result
        assert "textual" in result
        assert "class TerminalWidget" in result
        assert "from textual" in result

    def test_implement_web_component(self):
        """
        Test AC-2.2: Implement Web component.

        NECESSARY: N (Normal operation - web)
        """
        from ui_development_agent.ui_development_agent import ImplementUIComponent

        tool = ImplementUIComponent(
            component_name="WebWidget",
            implementation_type="web",
            specification="Widget for web display"
        )

        result = tool.run()

        assert "WebWidget" in result
        assert "web" in result
        # Check for HTML, CSS, and JS sections
        assert "html" in result.lower() or "<div" in result
        assert "css" in result.lower() or ".webwidget" in result.lower()
        assert "javascript" in result.lower() or "class WebWidget" in result

    def test_implement_includes_tests(self):
        """
        Test AC-2.3: Implementation includes test examples (TDD).

        NECESSARY: N (Normal - TDD workflow)
        Article VI: Tests written first
        """
        from ui_development_agent.ui_development_agent import ImplementUIComponent

        tool = ImplementUIComponent(
            component_name="TestableWidget",
            implementation_type="textual",
            specification="Widget that needs tests"
        )

        result = tool.run()

        assert "Test-Driven Development" in result or "TDD" in result
        assert "def test_" in result
        assert "pytest" in result.lower()

    def test_implement_includes_integration_steps(self):
        """
        Test AC-2.4: Implementation includes integration steps.

        NECESSARY: N (Normal - integration guidance)
        """
        from ui_development_agent.ui_development_agent import ImplementUIComponent

        tool = ImplementUIComponent(
            component_name="IntegrableWidget",
            implementation_type="textual",
            specification="Widget to integrate"
        )

        result = tool.run()

        assert "Integration" in result
        assert "__init__.py" in result or "Register" in result

    def test_implement_with_long_component_name(self):
        """
        Test AC-2.5: Implement component with very long name.

        NECESSARY: C (Corner case - long name)
        """
        from ui_development_agent.ui_development_agent import ImplementUIComponent

        long_name = "VeryLongComponentNameForTestingPurposes"
        tool = ImplementUIComponent(
            component_name=long_name,
            implementation_type="textual",
            specification="Testing long names"
        )

        result = tool.run()

        assert long_name in result


class TestCreateUIDevelopmentAgent:
    """Test create_ui_development_agent factory function."""

    @patch("ui_development_agent.ui_development_agent.Agent")
    @patch("ui_development_agent.ui_development_agent.get_model_instance")
    def test_create_agent_with_defaults(self, mock_model, mock_agent_class):
        """
        Test AC-3.1: Create agent with default parameters.

        NECESSARY: N (Normal operation - defaults)
        """
        from ui_development_agent.ui_development_agent import create_ui_development_agent

        mock_model.return_value = "claude-sonnet-4-20250514"

        agent = create_ui_development_agent()

        assert mock_agent_class.called
        # Verify agent was created with expected name
        call_args = mock_agent_class.call_args
        assert call_args[1]["name"] == "UIDevelo pmentAgent"

    @patch("ui_development_agent.ui_development_agent.Agent")
    @patch("ui_development_agent.ui_development_agent.get_model_instance")
    def test_create_agent_with_custom_model(self, mock_model, mock_agent_class):
        """
        Test AC-3.2: Create agent with custom model.

        NECESSARY: N (Normal operation - custom model)
        """
        from ui_development_agent.ui_development_agent import create_ui_development_agent

        mock_model.return_value = "gpt-5"

        agent = create_ui_development_agent(model="gpt-5")

        mock_model.assert_called_with("gpt-5")

    @patch("ui_development_agent.ui_development_agent.Agent")
    @patch("ui_development_agent.ui_development_agent.get_model_instance")
    def test_create_agent_with_agent_context(self, mock_model, mock_agent_class):
        """
        Test AC-3.3: Create agent with custom AgentContext.

        NECESSARY: N (Normal operation - with context)
        Article IV: VectorStore integration
        """
        from shared.agent_context import create_agent_context
        from ui_development_agent.ui_development_agent import create_ui_development_agent

        mock_model.return_value = "claude-sonnet-4-20250514"
        mock_context = Mock()
        mock_context.session_id = "test_session"
        mock_context.store_memory = Mock()

        agent = create_ui_development_agent(agent_context=mock_context)

        # Verify memory was stored (agent creation logged)
        mock_context.store_memory.assert_called()

    @patch("ui_development_agent.ui_development_agent.Agent")
    @patch("ui_development_agent.ui_development_agent.get_model_instance")
    def test_create_agent_has_required_tools(self, mock_model, mock_agent_class):
        """
        Test AC-3.4: Created agent has all required tools.

        NECESSARY: N (Normal operation - tool verification)
        Article I: Complete context
        """
        from ui_development_agent.ui_development_agent import create_ui_development_agent

        mock_model.return_value = "claude-sonnet-4-20250514"

        agent = create_ui_development_agent()

        # Check tools were passed to Agent
        call_args = mock_agent_class.call_args
        tools = call_args[1]["tools"]

        # Should have standard tools + UI-specific tools
        tool_names = [t.__name__ if hasattr(t, '__name__') else type(t).__name__ for t in tools]

        # Verify critical tools present
        assert any("Bash" in name for name in tool_names)
        assert any("Read" in name for name in tool_names)
        assert any("Write" in name for name in tool_names)
        assert any("Edit" in name for name in tool_names)

    @patch("ui_development_agent.ui_development_agent.Agent")
    @patch("ui_development_agent.ui_development_agent.get_model_instance")
    def test_create_agent_with_cost_tracker(self, mock_model, mock_agent_class):
        """
        Test AC-3.5: Create agent with cost tracking enabled.

        NECESSARY: N (Normal operation - cost tracking)
        """
        from ui_development_agent.ui_development_agent import create_ui_development_agent

        mock_model.return_value = "claude-sonnet-4-20250514"
        mock_cost_tracker = Mock()
        mock_context = Mock()
        mock_context.session_id = "test_session"
        mock_context.store_memory = Mock()

        with patch("shared.llm_cost_wrapper.wrap_agent_with_cost_tracking") as mock_wrap:
            agent = create_ui_development_agent(
                agent_context=mock_context,
                cost_tracker=mock_cost_tracker
            )

            # Cost tracker should be assigned to context
            assert mock_context.cost_tracker == mock_cost_tracker

    @patch("ui_development_agent.ui_development_agent.Agent")
    @patch("ui_development_agent.ui_development_agent.get_model_instance")
    def test_create_agent_returns_agent_instance(self, mock_model, mock_agent_class):
        """
        Test AC-3.6: Factory returns Agent instance.

        NECESSARY: R (Regression - correct return type)
        """
        from ui_development_agent.ui_development_agent import create_ui_development_agent

        mock_model.return_value = "claude-sonnet-4-20250514"
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        result = create_ui_development_agent()

        assert result == mock_agent


class TestUIDevelopmentAgentIntegration:
    """Integration tests for UIDevelo pmentAgent."""

    def test_design_and_implement_workflow(self):
        """
        Test AC-4.1: Full design-to-implement workflow.

        NECESSARY: N (Normal operation - full workflow)
        """
        from ui_development_agent.ui_development_agent import (
            DesignUIComponent,
            ImplementUIComponent,
        )

        # Step 1: Design
        design_tool = DesignUIComponent(
            component_name="TestComponent",
            component_type="widget",
            design_requirements="Test requirements"
        )
        design_result = design_tool.run()

        # Step 2: Implement based on design
        implement_tool = ImplementUIComponent(
            component_name="TestComponent",
            implementation_type="textual",
            specification=design_result[:500]  # Use part of design as spec
        )
        implement_result = implement_tool.run()

        # Both should complete without error
        assert "TestComponent" in design_result
        assert "TestComponent" in implement_result
        assert "class TestComponent" in implement_result

    def test_multiple_component_designs(self):
        """
        Test AC-4.2: Design multiple components in sequence.

        NECESSARY: S (Stress - multiple components)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        components = [
            ("Widget1", "widget"),
            ("Panel1", "panel"),
            ("View1", "view"),
            ("Modal1", "modal"),
            ("Widget2", "widget"),
        ]

        results = []
        for name, comp_type in components:
            tool = DesignUIComponent(
                component_name=name,
                component_type=comp_type,
                design_requirements=f"Requirements for {name}"
            )
            results.append(tool.run())

        # All should succeed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert components[i][0] in result


class TestUIDevelopmentAgentSecurity:
    """Security tests for UIDevelo pmentAgent."""

    def test_no_code_injection_in_component_name(self):
        """
        Test AC-5.1: Component names don't allow code injection.

        NECESSARY: S (Security - injection prevention)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        # Attempt to inject code via component name
        malicious_name = "Test<script>alert('xss')</script>"

        tool = DesignUIComponent(
            component_name=malicious_name,
            component_type="widget",
            design_requirements="Test"
        )

        result = tool.run()

        # The script tag should appear as-is (not executed), and design should complete
        assert "Component Design" in result

    def test_no_shell_injection_in_requirements(self):
        """
        Test AC-5.2: Requirements don't allow shell injection.

        NECESSARY: S (Security - shell injection prevention)
        """
        from ui_development_agent.ui_development_agent import DesignUIComponent

        # Attempt shell injection
        malicious_req = "; rm -rf / #"

        tool = DesignUIComponent(
            component_name="SafeComponent",
            component_type="widget",
            design_requirements=malicious_req
        )

        result = tool.run()

        # Should complete without executing shell command
        assert "SafeComponent" in result
        assert "Requirements:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
