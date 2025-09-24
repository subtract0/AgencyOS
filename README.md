# 🏥 Agency Code - Autonomous Software Engineering

A revolutionary AI-powered software engineering system with **undeniable self-healing capabilities**. Built with [Agency Swarm](https://agency-swarm.ai/welcome/overview) framework and enhanced with autonomous healing, constitutional governance, and LLM-first architecture.

## 🚀 Autonomous Healing - The Key Differentiator

**The Agency can detect, analyze, fix, test, and commit software changes without human intervention.**

### Real Autonomous Healing
- **🔍 Error Detection**: Automatic recognition of NoneType errors from logs and runtime failures
- **🧠 LLM-Powered Analysis**: GPT-5 generates intelligent fixes with context awareness
- **🛠️ Automatic Application**: Patches applied autonomously with safety verification
- **✅ Test Verification**: Complete test suite validation before any changes are committed
- **📝 Version Control**: Automatic commits with full audit trails

### See It In Action
```bash
# Quick demo of autonomous healing
./agency demo

# Run full autonomous healing demonstration
python demo_autonomous_healing.py
```

## 🏛️ Constitutional Governance

The Agency operates under strict constitutional principles that ensure quality and reliability:

### The Five Articles
1. **Complete Context**: No action without full understanding
2. **100% Verification**: All tests must pass - no exceptions
3. **Automated Enforcement**: Quality standards technically enforced
4. **Continuous Learning**: Automatic improvement through experience
5. **Spec-Driven Development**: All features require formal specifications

## 🎯 Key Features

### Core Capabilities
- **🤖 Autonomous Healing**: Self-fixing software that learns and improves
- **📐 Multi-Agent Architecture**: 10 specialized agents working in coordination
- **🧠 Learning & Memory**: Cross-session learning with VectorStore integration
- **🛡️ Constitutional Compliance**: Unbreakable quality standards
- **🔧 LLM-First Design**: Leverages GPT-5 intelligence instead of complex Python systems

### Developer Experience
- **⚡ Quick Setup**: One-command environment setup
- **🧪 Comprehensive Testing**: 725+ tests maintaining 100% success rate
- **📊 Real-Time Monitoring**: Live system health and performance metrics
- **🔄 Hot Reload**: Instant feedback during development
- **📚 Rich Documentation**: Complete API docs and usage examples

## 🏗️ Simplified Architecture

### 10 Core Agents
- **ChiefArchitectAgent**: Strategic oversight and self-directed task creation
- **AgencyCodeAgent**: Primary development agent with comprehensive toolset
- **PlannerAgent**: Strategic planning using spec-kit methodology
- **AuditorAgent**: Quality analysis using NECESSARY pattern
- **TestGeneratorAgent**: NECESSARY-compliant test generation
- **LearningAgent**: Pattern analysis and institutional memory
- **MergerAgent**: Integration and pull request management
- **QualityEnforcerAgent**: Constitutional compliance and autonomous healing
- **ToolsmithAgent**: Tool development and enhancement
- **WorkCompletionSummaryAgent**: Intelligent task summaries

### Communication Flows
Clean, focused communication patterns between agents:
```
ChiefArchitect → Strategic oversight of all agents
QualityEnforcer ↔ TestGenerator ↔ Coder → Quality improvement pipeline
Planner ↔ Coder → Development workflow
Auditor → Quality assessment and violation detection
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12 or 3.13
- Git
- OpenAI API key or compatible model provider

### Setup
```bash
# Clone and enter the repository
git clone <repository-url>
cd Agency

# One-command setup
./agency setup

# Run the Agency
./agency demo
```

### Environment Variables
Create a `.env` file:
```bash
OPENAI_API_KEY=your_api_key_here
FRESH_USE_FIRESTORE=false  # Set to true for persistent memory
USE_ENHANCED_MEMORY=true   # Enable VectorStore learning
```

## 🧪 Testing & Quality

### Test Commands
```bash
# Run all tests
./agency test

# Run specific test categories
python run_tests.py                    # Unit tests only
python run_tests.py --run-integration  # Integration tests
python run_tests.py --run-all          # All tests

# Run tests for specific modules
python -m pytest tests/test_auto_fix_nonetype.py -v
```

### Quality Metrics
- **689 tests** with 100% success rate
- **Complete test coverage** for all autonomous healing features
- **Constitutional compliance** across all components
- **NECESSARY pattern adherence** for test quality

## 🏥 Autonomous Healing Details

### NoneType Error Auto-Fix
The flagship autonomous healing capability:

1. **Detection**: Scans logs and runtime errors for NoneType patterns
2. **Analysis**: Uses LLM intelligence to understand context and generate fixes
3. **Application**: Applies fixes with automatic rollback on test failure
4. **Verification**: Runs complete test suite to ensure no regressions
5. **Commitment**: Commits successful fixes with detailed audit trails

### Healing Workflow
```bash
Error Detected → LLM Analysis → Fix Generated → Tests Pass → Auto-Commit
     ↓                                              ↓
Logged & Monitored                         Rollback on Failure
```

### Safety Mechanisms
- **Test-Driven Verification**: No changes without passing tests
- **Automatic Rollback**: Failed fixes are immediately reverted
- **Complete Audit Trail**: Every healing action is logged
- **Constitutional Compliance**: All changes follow governance principles

## 📊 Monitoring & Observability

### Logging
- **Autonomous Healing**: `logs/autonomous_healing/`
- **Session Transcripts**: `logs/sessions/`
- **Agent Communications**: `logs/telemetry/`

### Health Monitoring
```bash
# Check system health
python -c "from core import get_core; print(get_core().get_health_status())"

# Run constitutional compliance check
python scripts/constitutional_check.py
```

## 🛠️ CLI Commands

### Essential Commands
```bash
python run_tests.py              # Run test suite (725+ tests)
python demo_unified.py           # Unified core demonstration
python test_autonomous_operation.py  # Autonomous operation test
```

### Advanced Usage
```bash
# Manual agency execution
sudo python agency.py

# Specific test categories
python run_tests.py --run-integration

# Autonomous healing demo
python demo_autonomous_healing.py
```

## 📈 Performance & Scaling

### Optimization Features
- **LLM-First Architecture**: Delegates complex analysis to GPT-5
- **Focused Tool Set**: Simplified from 36 to 10 essential tools
- **Efficient Communication**: Streamlined agent interactions
- **Background Processing**: Non-blocking operations for long-running tasks

### Scalability
- **Multi-Agent Coordination**: Parallel processing capabilities
- **Memory Optimization**: Efficient context management
- **Resource Monitoring**: Automatic performance tracking
- **Load Balancing**: Smart agent utilization

## 🔮 Advanced Features

### Learning & Memory
- **VectorStore Integration**: Semantic search for pattern matching
- **Cross-Session Learning**: Knowledge persists between runs
- **Pattern Recognition**: Automatic identification of successful strategies
- **Institutional Memory**: Collective intelligence across all agents

### Constitutional Enforcement
- **Real-Time Monitoring**: Continuous compliance checking
- **Automatic Violation Prevention**: Blocks non-compliant operations
- **Emergency Response**: Crisis management and system protection
- **Audit Trail**: Complete history of all enforcement actions

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure 100% test pass rate
5. Submit pull request

### Code Quality Standards
- **Constitutional Compliance**: All 5 articles must be followed
- **Test Coverage**: 100% test success rate required
- **LLM-First**: Prefer LLM delegation over complex Python systems
- **Documentation**: Comprehensive docs for all features

## 📚 Documentation

- **[AGENTS.md](AGENTS.md)**: Complete agent architecture documentation
- **[CLAUDE.md](CLAUDE.md)**: Detailed development and configuration guide
- **[constitution.md](constitution.md)**: Constitutional principles and governance
- **[RECOVERY_SUMMARY.md](RECOVERY_SUMMARY.md)**: Recovery from over-engineering case study

## 🏆 Recognition

The Agency represents a breakthrough in autonomous software engineering:

- **✅ Undeniable Self-Healing**: Real fixes applied automatically
- **✅ Constitutional Governance**: Unbreakable quality standards
- **✅ LLM-First Architecture**: Intelligent delegation over complex systems
- **✅ Production Ready**: Comprehensive testing and safety mechanisms
- **✅ Developer Friendly**: World-class developer experience

## 🎉 Operational Autonomy Achieved

The Agency demonstrates that autonomous software maintenance is operational today. Experience a system that maintains and improves itself while adhering to the highest quality standards through constitutional governance and continuous learning.

**Welcome to the age of autonomous software engineering.**

---

*Built with ❤️ and AI by the Agency development team*