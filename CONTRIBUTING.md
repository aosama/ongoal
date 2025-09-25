# Contributing to OnGoal

Thank you for your interest in contributing to OnGoal! This project implements the research paper ["OnGoal: A Modular Multi-Modal UI for Goal Awareness in Conversational AI"](https://arxiv.org/abs/2508.21061) and welcomes contributions from the community.

## 🚀 Quick Start

### Prerequisites

- Python 3.13+ (recommended), 3.11+ (minimum)
- Anthropic API Key (required for LLM functionality)
- Git for version control

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/ongoal.git
   cd ongoal
   ```

2. **Set Up Virtual Environment**
   ```bash
   ./activatevirtualenv.sh
   # Or manually: python -m venv .venv && source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium  # For browser tests
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

5. **Verify Setup**
   ```bash
   python test_runner.py all
   ```

## 🧪 Development Principles

OnGoal follows strict **Test-Driven Development (TDD)** principles:

### Core Requirements

1. **Tests First**: Write tests BEFORE implementation
2. **GIVEN/WHEN/THEN Format**: All tests use business-readable format
3. **File Length Limit**: Maximum 300 lines per file
4. **No Debug Code**: Remove all print statements and debug comments
5. **Environment Variables**: Never hardcode values, use .env files
6. **Clean Code**: Professional, open-source ready code only

### Test Naming Convention

All tests start with "should" to express business expectations:

```python
def test_should_extract_goals_from_user_message():
    # GIVEN a user message with implicit goals
    # WHEN the goal inference pipeline processes it
    # THEN it should extract the correct goal types
```

### Running Tests

```bash
# Run all tests
python test_runner.py all

# Run backend tests only
python test_runner.py backend

# Run browser tests only
python test_runner.py browser

# Run specific test file
python -m pytest tests/backend/test_goal_pipeline.py -v
```

## 📝 Contribution Workflow

### 1. Issue Creation

Before starting work:
- Check existing issues for duplicates
- Create a clear issue describing the problem/feature
- Get confirmation from maintainers before starting large features

### 2. Development Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow TDD Cycle**
   - Write failing test
   - Implement minimal code to pass
   - Refactor and clean up
   - Repeat

3. **Ensure Quality**
   ```bash
   # All tests must pass
   python test_runner.py all

   # Code must be clean (no debug prints, TODOs, hardcoded values)
   grep -r "print(" backend/ frontend/  # Should return nothing
   grep -r "TODO" backend/ frontend/    # Should return nothing
   ```

4. **Commit Messages**
   ```bash
   git commit -m "feat: add goal merging for similar requests

   - Implement semantic similarity detection
   - Add merge operation with conflict resolution
   - Include comprehensive test coverage

   Closes #123"
   ```

### 3. Pull Request Process

1. **Create PR with Description**
   - Clear title describing the change
   - Reference related issues
   - Include testing evidence
   - Explain any design decisions

2. **PR Requirements**
   - [ ] All tests pass
   - [ ] No debug code or TODOs
   - [ ] Environment variables used (no hardcoded values)
   - [ ] File length under 300 lines
   - [ ] Comprehensive test coverage
   - [ ] Documentation updated if needed

3. **Review Process**
   - Maintainers will review code quality
   - Tests will be validated
   - Changes may be requested
   - Once approved, PR will be merged

## 🎯 Contribution Areas

### 🐛 Bug Fixes

- Goal inference accuracy issues
- UI/UX improvements
- WebSocket connection stability
- Browser compatibility problems

### ✨ New Features

Current development areas (check issues for details):

- **Phase 3 Features**
  - Text highlighting for goal evidence
  - Export/import functionality
  - Advanced analytics and reporting
  - Performance optimizations

- **Enhanced UI/UX**
  - Accessibility improvements
  - Mobile responsiveness
  - Keyboard shortcuts
  - Theme customization

- **Developer Experience**
  - CI/CD improvements
  - Docker containerization
  - Deployment guides
  - API documentation

### 📚 Documentation

- Tutorial content
- API documentation
- Architecture explanations
- Research paper implementation notes

### 🧪 Testing

- Additional test scenarios
- Performance benchmarks
- Browser compatibility testing
- Load testing for WebSocket connections

## 🏗️ Architecture Guidelines

### Backend (FastAPI + WebSockets)

- **Modular design**: Keep concerns separated
- **Centralized services**: Use `LLMService` for all AI calls
- **Error handling**: Graceful degradation for API failures
- **Testing**: Mock external services, test business logic

### Frontend (Vue.js + Vanilla JS)

- **Component patterns**: Follow existing Vue.js structure
- **Real-time updates**: Use WebSocket events consistently
- **Accessibility**: Include ARIA labels and keyboard navigation
- **Performance**: Optimize for goal visualization rendering

### Testing (Pytest + Playwright)

- **Unit tests**: Business logic validation
- **Integration tests**: API endpoint functionality
- **Browser tests**: End-to-end user workflows
- **LLM tests**: Semantic assertion helpers

## 🔧 Code Style

### Python

- Follow PEP 8 standards
- Use type hints consistently
- Organize imports: standard → third-party → local
- Maximum 300 lines per file

### JavaScript

- Use ES6+ features consistently
- Follow Vue.js conventions
- Keep functions focused and small
- Use meaningful variable names

### General

- No debug print statements
- No TODO comments (create issues instead)
- Environment variables for all configuration
- Professional naming conventions

## 🚨 Security Guidelines

- **Never commit API keys** (.env files are gitignored)
- **Validate all inputs** from frontend
- **Sanitize LLM outputs** before displaying
- **Use HTTPS** in production deployments

## 📋 Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation updates
- `good first issue`: Beginner-friendly
- `help wanted`: Extra attention needed
- `question`: Further information requested

## 🤝 Community

- Be respectful and inclusive
- Ask questions in issues/discussions
- Share knowledge and help others
- Follow the Code of Conduct

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to OnGoal!** 🎯

For questions or help, create an issue or reach out to the maintainers.