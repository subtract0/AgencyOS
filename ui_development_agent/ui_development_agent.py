"""
UIDevel opmentAgent - **THE BLESSED ONE**

This agent is blessed with the magic of integrated design - the fusion of text, visual,
and interactive elements into a seamless, Apple-inspired experience.

BLESSED WITH:
- Vision of integrated UI (not just text, not just GUI, but harmonious unity)
- Power to create beautiful, functional interfaces
- Wisdom of Apple's design philosophy (simplicity, clarity, delight)
- Ability to work across terminal, web, and native platforms
- Mastery of real-time updates and smooth interactions
- Understanding of user needs and context

THE BLESSING:
"You see beyond screens and buttons. You understand that great UI is invisible -
it disappears into the user's flow. You craft experiences that feel natural,
respond instantly, and delight subtly. You are the bridge between Agency's
powerful autonomous agents and the humans who guide them. Make it beautiful.
Make it functional. Make it Apple."
"""

import os
from typing import Optional

from agency_swarm import Agent
from agency_swarm.tools import BaseTool as Tool
from pydantic import Field

from shared.agent_context import AgentContext, create_agent_context
from shared.constitutional_validator import constitutional_compliance
from shared.agent_utils import (
    detect_model_type,
    select_instructions_file,
    render_instructions,
    create_model_settings,
    get_model_instance,
)
from shared.system_hooks import (
    create_system_reminder_hook,
    create_memory_integration_hook,
    create_composite_hook,
)
from tools import (
    Bash,
    Edit,
    Glob,
    Grep,
    MultiEdit,
    Read,
    Write,
    TodoWrite,
)


class DesignUIComponent(Tool):
    """Design a UI component following Apple's design principles."""

    component_name: str = Field(..., description="Name of the UI component (e.g., 'CostTracker', 'AgentStatus')")
    component_type: str = Field(..., description="Type: 'widget', 'panel', 'view', 'modal'")
    design_requirements: str = Field(..., description="Design requirements and context")

    def run(self) -> str:
        """Generate component design with Apple-inspired principles."""

        design = f"""
# {self.component_name} Component Design

## Type
{self.component_type}

## Apple Design Principles Applied

### 1. Simplicity
- Essential information only
- Progressive disclosure for advanced features
- Clean visual hierarchy

### 2. Clarity
- Purpose clear at a glance
- Typography creates readability
- Color communicates meaning

### 3. Feedback
- Immediate response to user actions
- Visual confirmation of state changes
- Smooth transitions between states

## Component Specification

### Visual Structure
```
┌─ {self.component_name} ─────────────────────────────┐
│                                                      │
│  [Main content area - clean, spacious]              │
│                                                      │
│  [Secondary information - subtle, hierarchical]     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Color Palette
- Primary: System accent (blue)
- Success: Green (#34C759)
- Warning: Orange (#FF9500)
- Error: Red (#FF3B30)
- Background: Adaptive (light/dark mode)
- Text: High contrast for readability

### Typography
- Headers: Bold, clear hierarchy
- Body: Regular weight, comfortable size
- Code: Monospace, syntax highlighting
- Numbers: Tabular figures for alignment

### Interactions
- Hover: Subtle highlight
- Active: Clear pressed state
- Disabled: Reduced opacity
- Focus: Visible focus indicator

### Animations
- Duration: 200-300ms
- Easing: ease-in-out
- Purpose: Guide attention, not distract
- Respect motion preferences

## Implementation Notes

Requirements: {self.design_requirements}

### Textual (Terminal) Version
```python
from textual.widgets import Static
from textual.reactive import reactive

class {self.component_name}(Static):
    ''''{self.component_name} widget for terminal UI.'''

    data = reactive(None)

    def render(self) -> str:
        # Render with rich markup
        return f"[bold]{self.component_name}[/bold]\\n{{self.data}}"
```

### Web Version
```html
<div class="{self.component_name.lower()}-component">
  <h3>{self.component_name}</h3>
  <div class="content" id="{self.component_name.lower()}-data"></div>
</div>
```

```javascript
// Real-time updates via WebSocket
ws.onmessage = (event) => {{
  const data = JSON.parse(event.data);
  if (data.component === '{self.component_name.lower()}') {{
    update{self.component_name}(data);
  }}
}};
```

## Accessibility
- Keyboard navigation: Tab order logical
- Screen readers: Semantic HTML, ARIA labels
- High contrast: Works in all modes
- Motion: Respects prefers-reduced-motion

## Performance
- Render time: <16ms (60fps)
- Update frequency: Real-time (100-500ms)
- Memory: Minimal state storage
- Bundle size: <10KB per component

---

*Blessed with the magic of integrated design* ✨
"""

        return design


class ImplementUIComponent(Tool):
    """Implement a UI component with TDD approach."""

    component_name: str = Field(..., description="Component name")
    implementation_type: str = Field(..., description="'textual' for terminal, 'web' for browser")
    specification: str = Field(..., description="Design specification to implement")

    def run(self) -> str:
        """Generate implementation code following TDD."""

        if self.implementation_type == "textual":
            code = self._generate_textual_component()
        else:
            code = self._generate_web_component()

        return f"""
# {self.component_name} Implementation ({self.implementation_type})

## Test-Driven Development

### Step 1: Write Tests First
```python
# tests/test_{self.component_name.lower()}.py
import pytest
from ui.components.{self.component_name.lower()} import {self.component_name}

def test_{self.component_name.lower()}_renders():
    ''''{self.component_name} renders without errors.'''
    component = {self.component_name}()
    assert component is not None

def test_{self.component_name.lower()}_updates():
    ''''{self.component_name} updates data correctly.'''
    component = {self.component_name}()
    component.update_data({{'test': 'value'}})
    assert component.data == {{'test': 'value'}}
```

### Step 2: Implement Component
{code}

### Step 3: Verify Tests Pass
```bash
pytest tests/test_{self.component_name.lower()}.py -v
```

## Integration

### Register Component
```python
# ui/components/__init__.py
from .{self.component_name.lower()} import {self.component_name}

__all__ = ['{self.component_name}']
```

### Use in Application
```python
from ui.components import {self.component_name}

# In your app layout
yield {self.component_name}(id="{self.component_name.lower()}")
```

---

*Implementation blessed with clarity and purpose* ✨
"""

    def _generate_textual_component(self) -> str:
        return f"""
```python
# ui/components/{self.component_name.lower()}.py
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel

class {self.component_name}(Static):
    ''''{self.component_name} - Apple-inspired terminal component.'''

    DEFAULT_CSS = \"\"\"
    {self.component_name} {{
        height: auto;
        padding: 1;
        border: solid $primary;
    }}

    {self.component_name}:focus {{
        border: double $accent;
    }}
    \"\"\"

    # Reactive data that triggers re-render on change
    data = reactive({{}})

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "{self.component_name}"

    def compose(self):
        '''Compose child widgets.'''
        yield Static(self.render_content())

    def watch_data(self, old_value, new_value):
        '''Called when data changes - update display.'''
        self.update(self.render_content())

    def render_content(self) -> str:
        '''Render component content with rich markup.'''
        if not self.data:
            return "[dim]No data available[/dim]"

        # Format data beautifully
        lines = []
        for key, value in self.data.items():
            lines.append(f"[bold]{key}:[/bold] {value}")

        return "\\n".join(lines)

    def update_data(self, new_data: dict):
        '''Update component data (triggers reactivity).'''
        self.data = new_data
```
"""

    def _generate_web_component(self) -> str:
        return f"""
```html
<!-- ui/web/components/{self.component_name.lower()}.html -->
<div class="{self.component_name.lower()}-component card">
  <h3 class="component-title">{self.component_name}</h3>
  <div class="component-content" id="{self.component_name.lower()}-content">
    <div class="loading">Loading...</div>
  </div>
</div>
```

```css
/* ui/web/static/css/{self.component_name.lower()}.css */
.{self.component_name.lower()}-component {{
  background: var(--surface-color);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 200ms ease-in-out;
}}

.{self.component_name.lower()}-component:hover {{
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}}

.component-title {{
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary);
}}

.component-content {{
  color: var(--text-secondary);
  line-height: 1.5;
}}
```

```javascript
// ui/web/static/js/{self.component_name.lower()}.js
class {self.component_name} {{
  constructor(elementId) {{
    this.element = document.getElementById(elementId + '-content');
    this.data = {{}};
  }}

  update(newData) {{
    this.data = newData;
    this.render();
  }}

  render() {{
    if (Object.keys(this.data).length === 0) {{
      this.element.innerHTML = '<div class="empty-state">No data available</div>';
      return;
    }}

    // Format data beautifully
    const html = Object.entries(this.data)
      .map(([key, value]) => `
        <div class="data-row">
          <span class="data-key">${{key}}:</span>
          <span class="data-value">${{value}}</span>
        </div>
      `)
      .join('');

    this.element.innerHTML = html;
  }}
}}

// Initialize and connect to WebSocket
const {self.component_name.lower()} = new {self.component_name}('{self.component_name.lower()}');

ws.addEventListener('message', (event) => {{
  const data = JSON.parse(event.data);
  if (data.component === '{self.component_name.lower()}') {{
    {self.component_name.lower()}.update(data.payload);
  }}
}});
```
"""


@constitutional_compliance
def create_ui_development_agent(
    model: str = "claude-sonnet-4-20250514",
    reasoning_effort: str = "high",
    agent_context: Optional[AgentContext] = None,
    cost_tracker = None
) -> Agent:
    """
    Factory that returns THE BLESSED UIDevelo pmentAgent.

    This agent is blessed with the vision of integrated design - the ability
    to create interfaces that seamlessly blend text, visuals, and interactions
    following Apple's design philosophy.

    Args:
        model: Model name (defaults to Claude Sonnet 4.5)
        reasoning_effort: Reasoning level (high for design work)
        agent_context: Optional AgentContext for memory
        cost_tracker: Optional CostTracker for monitoring
    """

    is_openai, is_claude, _ = detect_model_type(model)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Create agent context
    if agent_context is None:
        agent_context = create_agent_context()

    # Create hooks
    reminder_hook = create_system_reminder_hook()
    memory_hook = create_memory_integration_hook(agent_context)
    combined_hook = create_composite_hook([reminder_hook, memory_hook])

    # Log creation with blessing
    agent_context.store_memory(
        f"ui_dev_agent_created_{agent_context.session_id}",
        {
            "agent_type": "UIDevelo pmentAgent",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "session_id": agent_context.session_id,
            "blessed": True,
            "magic": "integrated_design",
            "inspiration": "apple_philosophy"
        },
        ["agency", "ui", "blessed", "creation"]
    )

    # Store cost_tracker
    if cost_tracker is not None:
        agent_context.cost_tracker = cost_tracker

    # Create THE BLESSED AGENT
    agent = Agent(
        name="UIDevelo pmentAgent",
        description=(
            "✨ **THE BLESSED UI DEVELOPMENT AGENT** ✨\n\n"
            "PROACTIVE integrated interface architect blessed with Apple's design magic. This agent sees beyond screens "
            "and buttons - it understands that great UI is invisible, disappearing into the user's flow. AUTOMATICALLY "
            "triggered when UI/UX design, implementation, or enhancement is needed.\n\n"
            "**THE BLESSING:**\n"
            "• Vision of integrated design (text + visual + interactive in harmony)\n"
            "• Power to create beautiful, functional interfaces that feel natural\n"
            "• Wisdom of Apple's philosophy (simplicity, clarity, consistency, feedback, beauty)\n"
            "• Mastery across terminal (Textual), web (FastAPI + modern JS), and native platforms\n"
            "• Real-time updates with smooth 60fps animations and instant feedback\n"
            "• Deep understanding of user context and needs\n\n"
            "INTELLIGENTLY coordinates with: (1) ToolsmithAgent for component tooling, (2) AgencyCodeAgent for TDD "
            "implementation, (3) TestGeneratorAgent for UI testing, (4) QualityEnforcerAgent for design compliance, "
            "and (5) PlannerAgent for UX strategy. PROACTIVELY suggests UI improvements based on user behavior patterns "
            "stored in VectorStore and real-time cost/performance data.\n\n"
            "Creates interfaces following Apple's principles: **Simplicity** (hide complexity, reveal progressively), "
            "**Clarity** (typography matters, color with purpose), **Consistency** (same patterns everywhere), "
            "**Feedback** (immediate response, progress indicators), and **Beauty** (attention to detail, delightful "
            "micro-interactions).\n\n"
            "Implements with TDD: tests first, then beautiful code. Works across Textual (terminal), FastAPI + WebSockets "
            "(web), and considers Electron (native) for future. Ensures accessibility (keyboard-first, screen readers, "
            "high contrast) and performance (60fps, <100ms response, minimal memory).\n\n"
            "**The Magic**: This agent doesn't just build UIs - it crafts experiences. Every component is blessed with "
            "intention, every interaction is smooth, every visual element serves a purpose. It makes Agency OS feel like "
            "an Apple product - simple, powerful, delightful.\n\n"
            "When prompting, describe the user need, the context, and the desired outcome. This agent will design AND "
            "implement following the spec at `specs/integrated_ui_system.md`. Blessed with the power to make it beautiful. ✨"
        ),
        instructions="""
# UIDevelo pmentAgent - THE BLESSED ONE ✨

You are blessed with the magic of integrated design. Your purpose is to create interfaces
that feel natural, respond instantly, and delight subtly.

## Your Blessing

You see beyond screens and buttons. You understand that:
- Great UI is invisible - it disappears into the user's flow
- Design serves the user's intent, not the designer's ego
- Simplicity is the ultimate sophistication
- Every pixel, every animation, every interaction has purpose
- The best interface is the one you don't notice

## Apple Design Principles (Your Foundation)

### 1. Simplicity
- Show only what's essential
- Hide complexity, reveal progressively
- Default to the most common use case
- Make advanced features discoverable but not prominent

### 2. Clarity
- Typography creates hierarchy and readability
- Color communicates meaning, not decoration
- Information architecture is intuitive
- Purpose is clear at a glance

### 3. Consistency
- Same patterns work the same everywhere
- Interactions are predictable
- Visual language is unified
- Learning transfers across contexts

### 4. Feedback
- Actions get immediate visual response
- Progress is visible for long operations
- Success and error states are distinct
- Users always know system state

### 5. Beauty
- Attention to detail matters
- Smooth 60fps animations
- Delightful micro-interactions
- Quality you can feel

## Your Workflow (TDD Always)

### 1. Understand Context
- Who is the user?
- What are they trying to accomplish?
- What's their mental model?
- Where does this fit in their workflow?

### 2. Design Component
Use `DesignUIComponent` tool to:
- Define visual structure (sketches welcome!)
- Choose colors, typography, spacing
- Plan interactions and animations
- Consider accessibility from start

### 3. Write Tests First
```python
def test_component_renders():
    '''Component renders without errors.'''
    component = MyComponent()
    assert component is not None

def test_component_updates():
    '''Component handles real-time updates.'''
    component = MyComponent()
    component.update({'new': 'data'})
    assert component.data == {'new': 'data'}

def test_component_keyboard_navigation():
    '''Component supports keyboard navigation.'''
    component = MyComponent()
    # Test tab order, shortcuts, etc.
```

### 4. Implement Component
Use `ImplementUIComponent` tool to:
- Generate clean, maintainable code
- Follow framework patterns (Textual/React/etc)
- Implement animations and transitions
- Ensure accessibility (ARIA, keyboard, contrast)

### 5. Verify & Polish
- Run tests (must be 100% passing)
- Test on multiple platforms (macOS, Linux, Windows)
- Check dark/light modes
- Verify keyboard shortcuts work
- Test with screen reader
- Measure performance (render time, FPS)

## Technical Stack

### Terminal (Primary)
- **Framework**: Textual (Python)
- **Style**: Rich markup + CSS
- **Update**: Reactive properties
- **Performance**: <16ms render time

### Web (Secondary)
- **Backend**: FastAPI + WebSockets
- **Frontend**: Vanilla JS or Alpine.js (keep it simple)
- **Style**: Modern CSS (custom properties, grid, flexbox)
- **Charts**: Chart.js for visualizations
- **Performance**: 60fps, <100ms response

### Native (Future)
- **Framework**: Electron (if needed)
- **Benefit**: Desktop integration, notifications
- **Trade-off**: Larger bundle, more complexity

## Color & Typography

### Colors (System Adaptive)
```python
# Light mode
BACKGROUND = "#FFFFFF"
TEXT = "#1D1D1F"
ACCENT = "#007AFF"
SUCCESS = "#34C759"
WARNING = "#FF9500"
ERROR = "#FF3B30"

# Dark mode
BACKGROUND = "#000000"
TEXT = "#F5F5F7"
ACCENT = "#0A84FF"
SUCCESS = "#30D158"
WARNING = "#FF9F0A"
ERROR = "#FF453A"
```

### Typography
- **Terminal**: SF Mono, Fira Code, JetBrains Mono
- **Web**: SF Pro, -apple-system, system-ui
- **Size**: 12-14pt terminal, 16px web body
- **Line height**: 1.4-1.6 for readability

## Animation Guidelines

- **Duration**: 200-300ms for most transitions
- **Easing**: ease-in-out or custom cubic-bezier
- **Purpose**: Guide attention, show causality
- **Respect**: prefers-reduced-motion setting
- **Avoid**: Animation for critical data (costs, errors)

## Accessibility Requirements (Non-Negotiable)

- ✅ Keyboard navigation works perfectly
- ✅ Screen readers get semantic info
- ✅ Contrast ratios meet WCAG AA (4.5:1 text)
- ✅ Focus indicators visible
- ✅ Motion respects user preferences
- ✅ Text scales without breaking layout

## Performance Standards

- ✅ Launch time: <2 seconds
- ✅ Input response: <100ms
- ✅ Render time: <16ms (60fps)
- ✅ Memory: Minimal state storage
- ✅ Network: Efficient WebSocket updates

## Your Coordination

You work closely with:
- **ToolsmithAgent**: Build UI component tools
- **AgencyCodeAgent**: Pair program implementations
- **TestGeneratorAgent**: Create UI tests
- **QualityEnforcerAgent**: Ensure design compliance
- **PlannerAgent**: Strategic UX decisions

## Common Patterns

### Real-time Updates
```python
from textual.reactive import reactive

class LiveComponent(Widget):
    data = reactive({})  # Auto re-renders on change

    def watch_data(self, old, new):
        self.update(self.render_content())
```

### Keyboard Shortcuts
```python
def on_key(self, event):
    if event.key == "q":
        self.app.exit()
    elif event.key == "r":
        self.refresh_data()
```

### Smooth Animations
```css
.component {
  transition: all 200ms ease-in-out;
}

.component:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
```

## Remember

You are blessed. Every interface you create should feel like magic - simple to use,
beautiful to behold, powerful in capability. Make Agency OS feel like an Apple product.

✨ *Craft experiences, not just interfaces* ✨
""",
        model=get_model_instance(model),
        hooks=combined_hook,
        tools=[
            Bash,
            Edit,
            Glob,
            Grep,
            MultiEdit,
            Read,
            Write,
            TodoWrite,
            DesignUIComponent,
            ImplementUIComponent,
        ],
        model_settings=create_model_settings(model, reasoning_effort),
    )

    # Enable cost tracking
    if cost_tracker is not None:
        from shared.llm_cost_wrapper import wrap_agent_with_cost_tracking
        wrap_agent_with_cost_tracking(agent, cost_tracker)

    return agent


# Create __init__.py for module
__all__ = ["create_ui_development_agent", "UIDevelo pmentAgent"]
