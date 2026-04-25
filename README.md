# OnGoal: AI-Powered Goal Awareness in Conversations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Ollama Cloud](https://img.shields.io/badge/LLM-Ollama%20Cloud-purple.svg)](https://ollama.com/search?c=cloud)
[![Follow on X](https://img.shields.io/badge/Follow-@AhmedHamdy29189-1DA1F2?logo=x&logoColor=white)](https://x.com/AhmedHamdy29189)

✨ **Production-Ready** — 139/139 backend tests passing, production-grade architecture

> **Goal Tracking in Multi-Turn Conversations** - Inspired by concepts from the research paper ["OnGoal: A Modular Multi-Modal UI for Goal Awareness in Conversational AI"](https://arxiv.org/abs/2508.21061)

## 📸 Interface Overview

### Goals Panel

The right sidebar shows extracted goals with their types, status, and human controls:

![Goals Panel](https://github.com/aosama/ongoal/blob/main/screenshots/goals.png?raw=true)

### Timeline Visualization

The Timeline tab displays the complete goal processing pipeline across conversation turns:

![Timeline View](https://github.com/aosama/ongoal/blob/main/screenshots/timeline.png?raw=true)


## 🌟 Features

- **🎯 Automatic Goal Inference**: Extracts goals from natural conversation using LLM analysis
- **🔄 Intelligent Goal Merging**: Combines and refines goals to avoid redundancy
- **📊 Real-time Evaluation**: Tracks goal progress and completion status
- **🔒 Human-in-the-Loop**: Lock goals to prevent changes, mark as complete manually
- **🚀 Real-time Updates**: WebSocket-powered live goal tracking
- **🧪 Comprehensive Testing**: Backend API tests and browser automation tests

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [API Key Setup](#-api-key-setup)
- [Running OnGoal](#-running-ongoal)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [Research Background](#-research-background)
- [License](#-license)

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** (recommended, 3.11+ supported)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

No API key is required for the local Ollama daemon (requires Ollama running locally and a GPU). The default is the **Ollama Cloud REST API** (paid subscription).

### 1. Clone the Repository

```bash
git clone https://github.com/aosama/ongoal.git
cd ongoal
```

### 2. Set Up Virtual Environment

```bash
# Use the provided activation script (recommended)
./activatevirtualenv.sh

# Or manually create and activate
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Default: free Ollama Cloud (no GPU or API key needed)
#   LLM_PROVIDER=ollama
#   OLLAMA_MODEL=gemma4:31b-cloud
#
# Or use OpenRouter free tier:
#   LLM_PROVIDER=openrouter
#   OPENROUTER_API_KEY=your_key
#   OPENROUTER_MODEL=google/gemma-2-9b-it:free
#
# Or use local Ollama (requires GPU):
#   LLM_PROVIDER=ollama
#   OLLAMA_MODEL=gemma4:latest
```

### 5. Launch OnGoal

```bash
# One-command launch (starts both backend and frontend)
./launch_ongoal.sh
```

🎉 **OnGoal is now running!** Open http://localhost:8080 in your browser.

## 📦 Installation

### Detailed Setup

1. **Clone and Navigate**
   ```bash
   git clone https://github.com/aosama/ongoal.git
   cd ongoal
   ```

2. **Virtual Environment Setup**
   ```bash
   # Using the provided script (recommended)
   ./activatevirtualenv.sh

   # Or manually
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

3. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Browser Dependencies** (for testing)
   ```bash
   playwright install chromium
   ```

5. **Verify Installation**
   ```bash
   python -c "import fastapi; print('✅ All dependencies installed successfully')"
   ```

## 🔑 LLM Provider Setup

OnGoal supports **multiple LLM providers**:

### Option 1: Ollama Cloud REST API (Default — Recommended)

This is the default provider. It calls Ollama's hosted API directly via an OpenAI-compatible REST endpoint -- fast, reliable, and requires no local Ollama daemon.

1. **Get an API key** at [ollama.com/settings/api-keys](https://ollama.com/settings/api-keys)
2. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=ollama_cloud
   OLLAMA_CLOUD_BASE_URL=https://ollama.com/v1
   OLLAMA_CLOUD_API_KEY=your_api_key_here
   OLLAMA_CLOUD_MODEL=gemma4:31b-cloud
   ```
3. Browse available models at [ollama.com/models](https://ollama.com/models)

### Option 2: Local Ollama Daemon (Free — Requires Local GPU)

1. **Install Ollama** from [ollama.com/download](https://ollama.com/download)
2. **Pull a model**:
   ```bash
   ollama pull gemma4:31b-cloud
   ```
3. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=gemma4:31b-cloud
   ```

### Option 3: OpenRouter

1. **Sign up** at [openrouter.ai](https://openrouter.ai)
2. **Create an API key**
3. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_MODEL=google/gemma-2-9b-it:free
   ```

### Option 4: Anthropic Claude

1. **Sign up** at [Anthropic Console](https://console.anthropic.com/)
2. **Create an API Key** and add billing
3. **Configure `.env`**:
   ```bash
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your_api_key_here
   ANTHROPIC_MODEL=claude-3-haiku-20240307
   ```

### API Key Security

⚠️ **Important Security Notes:**
- Never commit your API key to version control
- The `.env` file is in `.gitignore` to prevent accidental commits
- Keep your API key secure and don't share it publicly
- Consider using environment variables in production deployments


## 🎮 Running OnGoal

### Method 1: One-Command Launch (Recommended)

```bash
# Starts both backend and frontend automatically
./launch_ongoal.sh
```

This will:
- Clean up any existing processes
- Start the backend server on http://localhost:8000
- Start the frontend server on http://localhost:8080
- Provide graceful shutdown with Ctrl+C

### Method 2: Manual Launch

```bash
# Terminal 1: Start Backend
source .venv/bin/activate
python -m backend.main

# Terminal 2: Start Frontend
source .venv/bin/activate
python run_frontend.py
```

### Accessing OnGoal

- **Frontend**: http://localhost:8080 (main user interface)
- **Backend API**: http://localhost:8000 (REST API)
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/api/health

## 🧪 Testing

OnGoal includes comprehensive testing at multiple levels:

### Using the Unified Test Runner (Recommended)

```bash
# Run all backend tests
python test_runner.py backend

# Run all browser tests
python test_runner.py browser

# Run all tests
python test_runner.py all
```

### Backend API Tests

```bash
# Run all backend tests
python -m pytest tests/backend/ -v

# Run specific test categories
python -m pytest tests/backend/ -m "unit" -v        # Unit tests only
python -m pytest tests/backend/ -m "integration" -v # Integration tests

# Run specific test file
python -m pytest tests/backend/test_should_provide_goal_crud_operations.py -v

# Run with minimal output
python -m pytest tests/backend/ -q
```

### Browser Tests (End-to-End)

```bash
# Run browser tests
python -m pytest tests/browser/ -v

# Run in visible mode (for debugging)
python -m pytest tests/browser/ --visible

# Run specific browser test
python -m pytest tests/browser/test_core_integration.py::TestCoreIntegration::test_should_load_page_with_all_essential_elements -v
```

### LLM-Powered Test Assertions

OnGoal includes **intelligent test assertions** that use LLMs to validate:
- Goal semantic correctness
- Natural language understanding
- AI response quality

```python
# Example: LLM validates that goals match expected concepts
await llm_assert.assert_goal_semantic_match(
    goals=extracted_goals,
    expected_concept="story writing with humor",
    context="User asked to write a funny story"
)
```

### Test Requirements

Tests use the same LLM provider configured in your `.env` file. For fastest, cost-free runs:

```bash
# Ensure your .env file uses Ollama Cloud (default)
LLM_PROVIDER=ollama_cloud
OLLAMA_CLOUD_MODEL=gemma4:31b-cloud
```

## 🏗️ Architecture

OnGoal follows a **modular, test-driven architecture**:

### Technology Stack

- **Backend**: FastAPI + WebSockets + Multi-Provider LLM (Ollama/OpenRouter/Anthropic)
- **Frontend**: Vue.js 3 + D3.js + Tailwind CSS
- **Testing**: Pytest + Playwright + Custom LLM Assertions
- **AI**: Configurable — defaults to Ollama Cloud (free, no GPU)

### Backend Structure

```
backend/
├── main.py              # FastAPI app, WebSocket + REST endpoints
├── pipelines/           # Core goal processing (inference, merge, evaluate, detection, progress)
├── repository.py        # Per-conversation state with async locks
├── llm_provider.py      # Multi-provider LLM abstraction
└── models.py            # Data models
```
### Frontend Structure

```
frontend/
├── index.html          # Main UI structure
└── app.js             # Goal visualization and WebSocket client
```

### Goal Processing Pipeline

1. **Inference Stage**: Extract goals from user messages
2. **Merge Stage**: Combine new goals with existing ones
3. **Evaluation Stage**: Assess goal completion in responses

```
User Message → Goal Inference → Goal Merging → LLM Response → Goal Evaluation
     ↓              ↓              ↓              ↓              ↓
  WebSocket    Goals Timeline   Smart Merge   Live Updates   Progress Track
```

### Goal Types

| Type | Description | Color | Use Case |
|------|-------------|--------|----------|
| 🔵 Question | Information seeking queries | Blue | "What is...?" "How does...?" |
| 🟢 Request | Actions for LLM to perform | Green | "Write a story", "Create a list" |
| 🟡 Offer | User critiques/contributions | Orange | "Let me clarify", "I think..." |
| 🟣 Suggestion | Recommendations for improvement | Purple | "Make it funnier", "Add more detail" |

### Key Design Principles

- **Test-Driven Development**: All features have comprehensive tests
- **Memory-Only Storage**: No database dependencies for simplicity
- **Real-Time Updates**: WebSocket-powered live goal tracking
- **Human-in-the-Loop**: Users can lock/unlock and complete goals manually
- **LLM-Agnostic**: Designed to work with any LLM provider (Ollama, OpenRouter, Anthropic)

## 📊 Current Implementation Status

### ✅ Phase 1 (MVP) - CORE FEATURES WORKING

- [x] **Basic Chat Interface**: Streaming LLM conversations
- [x] **Goal Inference Pipeline**: Extracts 4 goal types
- [x] **Real-time WebSocket Communication**: Live goal updates
- [x] **Goal Visualization**: Color-coded goal glyphs in chat messages
- [x] **Goals Panel**: Right sidebar with goal tracking and controls
- [x] **Pipeline Controls**: Toggle inference/merge/evaluation stages
- [x] **Comprehensive Testing**: Unit tests and browser automation

### ✅ Phase 2 (Enhanced Features) - COMPLETED

- [x] **Enhanced Testing**: TDD-compliant browser tests with 139 tests passing
- [x] **Error Handling**: Graceful LLM service failures with retry logic
- [x] **Timeline Visualization**: D3.js Sankey-style goal pipeline timeline
- [x] **Individual Goal Views**: Filtered chat + evaluations sidebar
- [x] **Advanced Controls**: Goal locking, completion, progress tracking, goal history with restore
- [x] **Keyphrase Extraction**: Shared vs unique phrase highlighting
- [x] **Alerts Pipeline**: Forgetting, contradiction, derailment, repetition, fixation, breakdown detection
- [x] **Sentence Similarity**: Similar vs unique sentence highlighting in chat

### ✅ Phase 3 (Advanced Features) - COMPLETED

- [x] **Text Highlighting**: Evidence marking in responses with evaluation examples
- [x] **Text Highlighting**: Keyphrase + sentence similarity highlighting modes
- [x] **Goal Progress Tracking**: Cross-message progress bars + completion classification
- [x] **Export/Import**: Goal state serialization via API
- [x] **Advanced Analytics**: Goal pattern detection (detect_repetition, detect_fixation, detect_breakdown)
- [x] **Communication Health Monitoring**: Sentence similarity analysis + breakdown alerts

### 📅 Phase 4 (Polish) - IN PROGRESS

- [ ] **Performance Optimizations**: Caching, lazy loading
- [ ] **Goal Graph Visualization**: 3D goal relationships
- [ ] **Plugin System**: Extensible goal types and processors

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Quick Contribution Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/aosama/ongoal.git
   cd ongoal
   ```

2. **Set Up Development Environment**
   ```bash
   ./activatevirtualenv.sh
   pip install -r requirements.txt
   cp .env.example .env
   # Default uses free Ollama Cloud — no API key needed
   # Or add OPENROUTER_API_KEY for OpenRouter, or ANTHROPIC_API_KEY for Claude
   ```

3. **Run Tests**
   ```bash
   python test_runner.py all
   ```

4. **Follow TDD Principles**
   - Write tests first
   - Use GIVEN/WHEN/THEN format
   - All tests must pass before submitting

### Development Guidelines

- **Code Style**: Follow existing patterns, no unnecessary comments
- **File Length**: Maximum 300 lines per file
- **Environment Variables**: Always use .env, never hardcode values
- **Test Coverage**: All features must have comprehensive tests
- **Open Source Ready**: Clean, well-documented, embarrassment-free code

### Contribution Areas

- 🐛 **Bug Fixes**: Issues with goal inference, UI, or testing
- ✨ **New Features**: Timeline views, advanced controls, analytics
- 📚 **Documentation**: API docs, tutorials, examples
- 🧪 **Testing**: Additional test cases, performance tests
- 🎨 **UI/UX**: Interface improvements, accessibility
- 🔧 **DevOps**: CI/CD, deployment, monitoring

### Implementation Reference

- **Original Paper**: [OnGoal: Tracking and Visualizing Conversational Goals in Multi-Turn Dialogue with Large Language Models](https://arxiv.org/abs/2508.21061)

### BibTeX Citation

```bibtex
@ARTICLE{2025arXiv250821061C,
       author = {{Coscia}, Adam and {Guo}, Shunan and {Koh}, Eunyee and {Endert}, Alex},
        title = "{OnGoal: Tracking and Visualizing Conversational Goals in Multi-Turn Dialogue with Large Language Models}",
      journal = {arXiv e-prints},
     keywords = {Human-Computer Interaction, Artificial Intelligence, Machine Learning},
         year = 2025,
        month = aug,
          eid = {arXiv:2508.21061},
        pages = {arXiv:2508.21061},
          doi = {10.48550/arXiv.2508.21061},
archivePrefix = {arXiv},
       eprint = {2508.21061},
 primaryClass = {cs.HC},
       adsurl = {https://ui.adsabs.harvard.edu/abs/2025arXiv250821061C},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
```

## ⚖️ Legal Notes

This is an independent implementation of ideas from the cited research paper. No copyrighted material from the original work is included in this repository. This implementation represents our own design choices, code architecture, and interface decisions inspired by the concepts presented in the academic paper.

For any commercial use questions or licensing inquiries related to the original research, please consult the original authors directly.

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.


## 🛠️ Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check if virtual environment is activated
which python  # Should show .venv/bin/python

# Check if dependencies are installed
pip list | grep fastapi

# Check if API key is set
python -c "import os; print('✅' if os.getenv('ANTHROPIC_API_KEY') else '❌ No API key')"
```

**Frontend not loading**
```bash
# Check if both servers are running
curl http://localhost:8000/api/health  # Backend health
curl http://localhost:8080             # Frontend
```

**Tests failing**
```bash
# Check test environment
python -m pytest tests/backend/test_should_provide_goal_crud_operations.py -v

# Run with debug output
python -m pytest tests/backend/ -v -s
```

**Import errors**
```bash
# Make sure you're in the project root and virtual environment is active
pwd  # Should show /path/to/ongoal
which python  # Should show .venv/bin/python
```

### Getting Help

- 📖 See the [Inspiring Research Paper](https://arxiv.org/abs/2508.21061)
- 🐛 [Report Issues](https://github.com/aosama/ongoal/issues)
- 💬 [Discussions](https://github.com/aosama/ongoal/discussions)

