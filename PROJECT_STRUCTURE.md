# 🏗️ Project Structure & Development Guide

## 📁 Repository Structure

```
legalizeme-agent-rag-v1/
├── 📱 app/                          # Main application
│   ├── agents/                      # AI agent orchestration
│   │   ├── __init__.py
│   │   └── counsel_agent.py         # Main legal AI agent
│   ├── api/                         # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── main.py                  # Primary API routes
│   │   ├── crawler.py               # Web crawling endpoints
│   │   └── performance.py           # Performance monitoring
│   ├── crawlers/                    # Web crawling modules
│   │   ├── __init__.py
│   │   ├── kenya_law_crawler.py     # Kenya Law website crawler
│   │   └── scheduler.py             # Crawling scheduler
│   ├── evaluation/                  # Model evaluation
│   │   ├── __init__.py
│   │   └── test_counsel.py          # Agent evaluation tests
│   ├── indexing/                    # Search indexing
│   │   ├── __init__.py
│   │   └── enhanced_indexer.py      # Enhanced search indexer
│   ├── optimization/                # Performance optimization
│   │   ├── __init__.py
│   │   ├── llm_optimizer.py         # LLM performance optimizer
│   │   ├── performance_optimizer.py # General performance optimizer
│   │   └── vector_store_optimizer.py # Vector store optimizer
│   ├── parsers/                     # Document processing
│   │   ├── __init__.py
│   │   ├── document_parser.py       # PDF/DOCX parsing
│   │   ├── document_processor_enhanced.py # Enhanced document processor
│   │   └── web_parser.py            # Web content parsing
│   ├── rag/                         # RAG (Retrieval-Augmented Generation)
│   │   ├── __init__.py
│   │   ├── legal_reasoner.py        # Legal reasoning engine
│   │   └── retriever.py             # Document retrieval
│   ├── summarization/               # Document summarization
│   │   ├── __init__.py
│   │   └── document_summarizer.py   # Legal document summarizer
│   ├── utils/                       # Core utilities
│   │   ├── stubs/                   # Module stubs for missing dependencies
│   │   ├── __init__.py
│   │   ├── claude_model.py          # Claude 4 integration
│   │   ├── hunyuan_model.py         # Hunyuan A13B integration
│   │   ├── invoke_method.py         # Method invocation utilities
│   │   ├── llm_factory.py           # LLM factory pattern
│   │   ├── llm_router.py            # Multi-model routing
│   │   ├── logger.py                # Logging utilities
│   │   ├── module_stubs.py          # Module stub loader
│   │   ├── patch_imports.py         # Import patching system
│   │   └── prompts.py               # AI prompts
│   ├── __init__.py
│   └── main.py                      # Application entry point
├── 🧪 tests/                        # Test suites
│   ├── __init__.py
│   └── test_hunyuan.py              # Hunyuan model tests
├── 📜 scripts/                      # Development scripts
│   ├── dev-setup.sh                 # Development environment setup
│   ├── dev-start.sh                 # Start development server
│   ├── dev-test.sh                  # Run test suite
│   ├── dev-clean.sh                 # Clean development artifacts
│   ├── smoke_test_claude.py         # Claude API smoke tests
│   └── test_multi_llm.py            # Multi-LLM integration tests
├── ☁️ copilot/                      # AWS Copilot deployment
│   ├── api/
│   │   └── manifest.yml             # Service deployment config
│   └── README.md                    # Deployment guide
├── ⚙️ .github/                      # GitHub Actions
│   └── workflows/
│       └── backend-ci.yml           # CI/CD pipeline
├── 📊 data/                         # Data storage
│   ├── vector_db/                   # Vector database
│   ├── model_cache/                 # Model cache
│   ├── temp_pdfs/                   # Temporary PDF storage
│   └── llm_config/                  # LLM configuration
├── 📋 requirements.txt              # Python dependencies
├── 🐳 Dockerfile.ci                 # Docker configuration
├── 🔧 .env.example                  # Environment variables template
├── 📝 .gitignore                    # Git ignore rules
├── 📚 README.md                     # Main documentation
├── 🤖 MULTI_LLM_IMPLEMENTATION.md   # Multi-LLM technical guide
└── 🏗️ PROJECT_STRUCTURE.md          # This file
```

## 🚀 Quick Start for Developers

### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/joshuarebo/legalizeme-agent-rag-v1.git
cd legalizeme-agent-rag-v1

# Run automated setup
./scripts/dev-setup.sh

# Start development server
./scripts/dev-start.sh
```

### 2. Available Commands
```bash
# Development lifecycle
./scripts/dev-setup.sh    # Initial setup
./scripts/dev-start.sh    # Start server
./scripts/dev-test.sh     # Run tests
./scripts/dev-clean.sh    # Clean artifacts

# Testing variations
./scripts/dev-test.sh unit         # Unit tests only
./scripts/dev-test.sh integration  # Integration tests only
./scripts/dev-test.sh api          # API tests only

# Cleanup variations
./scripts/dev-clean.sh --all      # Clean everything
./scripts/dev-clean.sh --cache    # Clean cache only
./scripts/dev-clean.sh --logs     # Clean logs only
```

## 🔧 Configuration

### Environment Variables
Create `.env` file from `.env.example`:
```bash
# Required for production
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

# Optional for enhanced features
HUGGINGFACE_API_KEY=your_hf_key
OPENAI_API_KEY=your_openai_key

# Development settings
DEBUG_MODE=true
PRIMARY_LLM_TYPE=flan-t5  # For development
```

### Model Configuration
- **Development**: Uses `flan-t5` (lightweight, fast)
- **Staging**: Uses `claude-4` + `flan-t5` (balanced)
- **Production**: Uses all models with intelligent routing

## 🧠 AI Model Integration

### Available Models
1. **Claude 4** - Advanced reasoning, analysis
2. **Hunyuan A13B** - Multilingual, efficient
3. **FLAN-T5** - Development, simple tasks
4. **Mixtral** - General purpose
5. **LLaMA** - Reasoning tasks

### Model Routing
- Automatic selection based on query complexity
- Fallback chain for reliability
- Cost optimization by environment

## 🔌 API Endpoints

### Core Endpoints
- `GET /models` - List available models
- `POST /query` - Legal Q&A with model selection
- `POST /summarize` - Document summarization
- `POST /draft` - Legal document drafting
- `GET /health` - Service health check

### Usage Example
```javascript
// Query with model selection
fetch('/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "What are employment termination requirements in Kenya?",
    model: "claude-4",
    temperature: 0.3
  })
});
```

## 🏗️ Architecture Overview

### Request Flow
1. **API Layer** (`app/api/`) - FastAPI endpoints
2. **Router Layer** (`app/utils/llm_router.py`) - Model selection
3. **Agent Layer** (`app/agents/`) - AI orchestration
4. **RAG Layer** (`app/rag/`) - Document retrieval
5. **Model Layer** (`app/utils/`) - AI model interfaces

### Key Components
- **LLM Router**: Intelligent model selection
- **Counsel Agent**: Legal reasoning workflow
- **Document Parser**: PDF/DOCX processing
- **Vector Store**: Semantic search
- **Crawler**: Legal data collection

## 🧪 Testing Strategy

### Test Types
1. **Unit Tests** - Individual component testing
2. **Integration Tests** - Multi-component testing
3. **API Tests** - Endpoint testing
4. **Smoke Tests** - Quick health checks

### Test Execution
```bash
# Run specific test types
./scripts/dev-test.sh unit
./scripts/dev-test.sh integration
./scripts/dev-test.sh api

# Run all tests
./scripts/dev-test.sh all
```

## 📦 Deployment

### Local Development
```bash
# Start development server
./scripts/dev-start.sh

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### AWS Copilot (Production)
```bash
# Deploy to AWS
copilot svc deploy --name api --env prod

# See deployment guide
cat copilot/README.md
```

### Docker
```bash
# Build image
docker build -f Dockerfile.ci -t legalizeme-backend .

# Run container
docker run -p 8000:8000 legalizeme-backend
```

## 🔍 Code Organization Principles

### Directory Structure
- **Single Responsibility**: Each directory has a clear purpose
- **Separation of Concerns**: API, business logic, and utilities separated
- **Modular Design**: Easy to extend and maintain

### File Naming
- **Descriptive Names**: Clear purpose from filename
- **Consistent Patterns**: Similar files follow same naming
- **No Legacy Files**: Removed all outdated/duplicate files

### Import Structure
```python
# Standard library imports
import os
import json

# Third-party imports
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from app.utils.llm_router import LLMRouter
from app.agents.counsel_agent import CounselAgent
```

## 🚨 Removed During Cleanup

### Files Removed
- 25+ test files from root directory
- 15+ batch/shell scripts
- 5+ duplicate requirements files
- 3+ obsolete documentation files
- Multiple "fixed" versions of files
- Unused MCP server directory

### Why Removed
- **Clutter**: Made navigation difficult
- **Confusion**: Multiple versions of same files
- **Maintenance**: Outdated scripts and configs
- **Standards**: Not following best practices

## 🤝 Frontend Integration

### API Integration
```typescript
// lib/api.ts
export class LegalizeAPI {
  async query(params: QueryParams) {
    // Query implementation
  }
  
  async getModels() {
    // Get available models
  }
}
```

### Error Handling
```typescript
try {
  const result = await api.query(params);
  if (result.error) {
    // Handle API errors
  }
} catch (error) {
  // Handle network errors
}
```

## 📈 Performance Considerations

### Development
- Uses lightweight models (FLAN-T5)
- Minimal resource usage
- Fast startup times

### Production
- Intelligent model routing
- Response caching
- Auto-scaling with AWS Copilot

## 🛡️ Security Features

### Production Security
- AWS IAM integration
- Secrets management
- HTTPS/TLS encryption
- Input validation
- Rate limiting

### Development Security
- Environment variable isolation
- No hardcoded secrets
- Secure defaults

## 📚 Additional Resources

- [README.md](README.md) - Main documentation
- [MULTI_LLM_IMPLEMENTATION.md](MULTI_LLM_IMPLEMENTATION.md) - Technical details
- [copilot/README.md](copilot/README.md) - Deployment guide
- [API Documentation](http://localhost:8000/docs) - Interactive API docs

---

**🎯 Ready to Code!**

This structure provides a solid foundation for rapid development while maintaining production-quality standards. The frontend team can now easily integrate with the clean API structure, and the backend team can extend functionality without confusion.

**Next Steps:**
1. Run `./scripts/dev-setup.sh` to get started
2. Review API documentation at `/docs`
3. Check model availability at `/models`
4. Start building awesome features! 🚀