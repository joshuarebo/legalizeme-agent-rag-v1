# 🏛️ LegalizeMe AI Agent

> **Advanced Multi-LLM Legal AI Assistant for Kenyan Law**  
> Production-ready FastAPI backend with intelligent model routing, AWS deployment, and comprehensive legal document processing.

[![CI/CD](https://github.com/joshuarebo/legalizeme-agent-rag-v1/workflows/Backend%20CI/badge.svg)](https://github.com/joshuarebo/legalizeme-agent-rag-v1/actions)
[![AWS Copilot](https://img.shields.io/badge/AWS-Copilot-orange)](https://aws.github.io/copilot-cli/)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)

## 🚀 Quick Start

### Frontend Integration

```bash
# Production API Endpoint
BASE_URL="https://your-api-domain.com"

# Development
BASE_URL="http://localhost:8000"
```

### Key Endpoints for Frontend

```typescript
// Model Selection
GET  /models                 // List available AI models
POST /query                  // Legal question answering
POST /summarize              // Document summarization  
POST /draft                  // Legal document drafting
GET  /health                 // Service health check
```

### Example API Usage

```javascript
// Query with model selection
const response = await fetch(`${BASE_URL}/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "What are the employment termination requirements in Kenya?",
    model: "claude-4",           // AI model choice
    temperature: 0.3,            // Response creativity (0-1)
    max_tokens: 2048            // Response length limit
  })
});

// Get available models
const models = await fetch(`${BASE_URL}/models`).then(r => r.json());
console.log(models.available_models); 
// ["claude-4", "hunyuan-a13b", "flan-t5", "mixtral", "llama"]
```

## 🧠 AI Models Available

| Model | Best For | Speed | Cost | Context |
|-------|----------|-------|------|---------|
| **Claude 4** | Complex legal analysis, reasoning | ⚡⚡⚡ | 💰💰💰 | 200K tokens |
| **Hunyuan A13B** | Multilingual legal queries | ⚡⚡ | 💰💰 | 32K tokens |
| **FLAN-T5** | Development, simple Q&A | ⚡⚡⚡⚡ | 💰 | 2K tokens |
| **Mixtral** | General legal questions | ⚡⚡ | 💰💰 | 32K tokens |
| **LLaMA 3** | Reasoning, analysis | ⚡⚡ | 💰💰 | 8K tokens |

## 📁 Project Structure

```
legalizeme-agent-rag-v1/
├── 🏗️  app/                     # Main application
│   ├── agents/                  # AI agent orchestration
│   │   └── counsel_agent.py     # Main legal AI agent
│   ├── api/                     # FastAPI endpoints
│   │   ├── main.py             # Primary API routes
│   │   ├── crawler.py          # Web crawling endpoints
│   │   └── performance.py      # Performance monitoring
│   ├── utils/                   # Core utilities
│   │   ├── llm_router.py       # Multi-model routing
│   │   ├── claude_model.py     # Claude 4 integration
│   │   ├── hunyuan_model.py    # Hunyuan A13B integration
│   │   └── llm_factory.py      # Model factory
│   ├── rag/                     # Retrieval-Augmented Generation
│   │   ├── retriever.py        # Document retrieval
│   │   └── legal_reasoner.py   # Legal reasoning engine
│   ├── parsers/                 # Document processing
│   │   ├── document_parser.py  # PDF/DOCX processing
│   │   └── web_parser.py       # Web content parsing
│   └── optimization/            # Performance optimization
├── 🧪 tests/                    # Test suites
├── 📜 scripts/                  # Utility scripts
├── ☁️  copilot/                 # AWS deployment config
├── ⚙️  .github/                 # CI/CD workflows
└── 📊 data/                     # Data storage
```

## 🛠️ Development Setup

### Prerequisites

- **Python 3.11+**
- **Docker** (for containerization)
- **AWS CLI** (for deployment)
- **Git**

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/joshuarebo/legalizeme-agent-rag-v1.git
cd legalizeme-agent-rag-v1

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
cp .env.example .env  # Create and configure

# 5. Start development server
python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

```env
# Required for production
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1

# Optional API keys (for enhanced models)
HUGGINGFACE_API_KEY=your_hf_key
OPENAI_API_KEY=your_openai_key

# Application settings
DEBUG_MODE=true
PRIMARY_LLM_TYPE=claude-4
MODEL_CACHE_DIR=./data/model_cache
```

## 🚀 Deployment

### AWS Copilot (Production)

```bash
# 1. Initialize AWS Copilot
copilot app init legalizeme-ai
cd legalizeme-ai

# 2. Deploy to production
copilot svc deploy --name api --env prod

# 3. Get service URL
copilot svc show --name api --env prod
```

### Docker (Development)

```bash
# Build and run
docker build -f Dockerfile.ci -t legalizeme-backend .
docker run -p 8000:8000 -e HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY legalizeme-backend
```

## 🔗 API Reference

### Authentication
Currently, the API is **open** for development. Production deployments should implement proper authentication.

### Core Endpoints

#### `POST /query` - Legal Question Answering
Submit legal questions and get AI-powered answers.

```typescript
interface QueryRequest {
  query: string;                    // Legal question
  model?: string;                   // AI model ("claude-4", "flan-t5", etc.)
  temperature?: number;             // 0.0-1.0, controls creativity
  max_tokens?: number;              // Response length limit
  system_prompt?: string;           // Custom system instructions
  urls?: string[];                  // Additional web sources
}

interface QueryResponse {
  response: string;                 // AI-generated answer
  model_used: string;              // Which model was used
  confidence_score?: number;        // Response confidence (0-1)
  citations?: Citation[];          // Legal references
  error?: string;                  // Error message if any
}
```

#### `POST /summarize` - Document Summarization
Summarize legal documents or web pages.

```typescript
interface SummarizeRequest {
  query?: string;                   // Specific focus for summary
  model?: string;                   // AI model choice
  urls?: string[];                  // Web pages to summarize
  // + file upload via multipart/form-data
}
```

#### `POST /draft` - Legal Document Drafting
Generate legal documents based on context.

```typescript
interface DraftRequest {
  document_type: string;            // Type of document to draft
  context: string;                  // Context and requirements
  model?: string;                   // AI model choice
  urls?: string[];                  // Reference materials
}
```

#### `GET /models` - Available AI Models
List all available AI models and their capabilities.

```typescript
interface ModelsResponse {
  available_models: string[];       // Model names
  model_details: {                 // Model specifications
    [key: string]: {
      context_length: number;
      max_tokens: number;
      strengths: string[];
      use_cases: string[];
    }
  };
  default_model: string;           // Default model name
}
```

## 🧪 Testing

### Run Test Suite

```bash
# Full test suite
python scripts/test_multi_llm.py

# Quick smoke tests
python scripts/smoke_test_claude.py

# Unit tests
pytest tests/ -v

# API integration tests
python -m pytest tests/test_api_integration.py
```

### Model-Specific Testing

```bash
# Test Claude 4
python -c "
import asyncio
from app.utils.llm_router import route_model
result = asyncio.run(route_model('Test query', 'claude-4'))
print(result)
"

# Test all models
python scripts/test_multi_llm.py --comprehensive
```

## 📊 Performance & Monitoring

### Performance Characteristics

| Metric | Development | Production |
|--------|-------------|------------|
| **Cold Start** | ~2-5s | ~1-3s |
| **Response Time** | ~1-8s | ~0.5-5s |
| **Concurrent Users** | 10+ | 100+ |
| **Memory Usage** | 2-4GB | 4-8GB |

### Monitoring

- **Health Check**: `GET /health`
- **CloudWatch**: AWS metrics and logs
- **Performance**: Built-in response time tracking
- **Error Tracking**: Structured logging

## 🔒 Security

### Production Security Features

- ✅ **AWS IAM** integration
- ✅ **Secrets Manager** for API keys
- ✅ **VPC private placement**
- ✅ **HTTPS/TLS** encryption
- ✅ **Rate limiting** (configurable)
- ✅ **Input validation** on all endpoints

### Security Headers

```typescript
// Recommended frontend security headers
{
  'Content-Security-Policy': "default-src 'self'",
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin'
}
```

## 🤝 Frontend Integration Guide

### React/Next.js Example

```typescript
// lib/api.ts
export class LegalizeAPI {
  constructor(private baseUrl: string) {}

  async query(params: {
    query: string;
    model?: string;
    temperature?: number;
  }) {
    const response = await fetch(`${this.baseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return response.json();
  }

  async getModels() {
    const response = await fetch(`${this.baseUrl}/models`);
    return response.json();
  }
}

// Usage in component
const api = new LegalizeAPI(process.env.NEXT_PUBLIC_API_URL);
const result = await api.query({
  query: "What are my rights as an employee in Kenya?",
  model: "claude-4"
});
```

### Error Handling

```typescript
try {
  const result = await api.query({ query: "legal question" });
  if (result.error) {
    // Handle API errors
    console.error('API Error:', result.error);
  }
} catch (error) {
  // Handle network errors
  console.error('Network Error:', error);
}
```

### Model Selection UI

```typescript
// Recommended UI for model selection
const ModelSelector = () => {
  const [models, setModels] = useState([]);
  
  useEffect(() => {
    api.getModels().then(data => setModels(data.available_models));
  }, []);

  return (
    <select>
      {models.map(model => (
        <option key={model} value={model}>
          {model} {model === 'claude-4' && '(Recommended)'}
        </option>
      ))}
    </select>
  );
};
```

## 📈 Scalability

### Auto-Scaling (AWS Copilot)

- **Min instances**: 1 (dev), 2 (prod)
- **Max instances**: 3 (dev), 5 (prod)
- **Scale triggers**: CPU > 70%, Memory > 80%

### Cost Optimization

| Environment | Monthly Cost | Models Used |
|-------------|--------------|-------------|
| **Development** | $50-100 | FLAN-T5, Mixtral |
| **Staging** | $100-200 | Claude 4, FLAN-T5 |
| **Production** | $300-500+ | All models |

*Note: Costs exclude AWS Bedrock usage (Claude 4) which depends on volume*

## 🛟 Support & Troubleshooting

### Common Issues

#### **Model Access Denied**
```bash
# Enable Bedrock access in AWS Console
aws bedrock list-foundation-models --region us-east-1
```

#### **High Latency**
- Use FLAN-T5 for development/testing
- Enable response caching (included)
- Check CloudWatch metrics

#### **Memory Issues**
- Increase container memory in `copilot/api/manifest.yml`
- Use 4-bit quantization (already configured)

### Support Channels

- 🐛 **Issues**: [GitHub Issues](https://github.com/joshuarebo/legalizeme-agent-rag-v1/issues)
- 📚 **Documentation**: [Multi-LLM Implementation Guide](./MULTI_LLM_IMPLEMENTATION.md)
- 🚀 **Deployment**: [Copilot Guide](./copilot/README.md)

## 🤖 AI Model Details

### Model Routing Logic

The system automatically selects the best model based on:
- **Query complexity** (simple → FLAN-T5, complex → Claude 4)
- **Language** (multilingual → Hunyuan A13B)
- **Cost optimization** (development → lighter models)
- **Fallback chain** (primary fails → backup models)

### Model Capabilities

```python
# Model strengths and use cases
MODEL_CAPABILITIES = {
    "claude-4": {
        "strengths": ["reasoning", "analysis", "safety", "long_context"],
        "best_for": ["complex_legal_analysis", "document_review", "ethical_reasoning"]
    },
    "hunyuan-a13b": {
        "strengths": ["multilingual", "reasoning", "efficiency"],
        "best_for": ["multilingual_legal", "chinese_law", "cost_optimization"]
    },
    "flan-t5": {
        "strengths": ["instruction_following", "summarization", "speed"],
        "best_for": ["development", "simple_qa", "classification"]
    }
}
```

## 📋 Changelog

### v2.0.0 - Multi-LLM Implementation
- ✅ Added 6 AI model support with intelligent routing
- ✅ Integrated Claude 4 via Amazon Bedrock
- ✅ Added Hunyuan A13B with quantization
- ✅ Enhanced API with model selection
- ✅ Complete AWS Copilot deployment
- ✅ Comprehensive testing suite

### v1.0.0 - Initial Release
- ✅ FastAPI backend with legal document processing
- ✅ Basic LLM integration
- ✅ Document parsing and RAG

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for the Kenyan legal community**  
*Empowering legal professionals with AI-driven insights and document automation*
