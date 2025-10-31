# LLM Provider Configuration Guide

The Amazon Product Analysis Agent supports multiple LLM providers, allowing you to choose the AI model that best fits your needs and budget.

## Supported Providers

| Provider | Models | Cost | Setup Difficulty |
|----------|--------|------|------------------|
| **Google Gemini** (Default) | gemini-2.0-flash-exp, gemini-2.5-flash, gemini-1.5-pro | Free tier available | Easy |
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo | Paid | Easy |
| **Anthropic Claude** | claude-3-5-sonnet, claude-3-opus | Paid | Easy |
| **Ollama** (Local) | llama3.1, mistral, codellama | Free (local) | Medium |
| **Groq** | llama-3.3-70b-versatile, mixtral-8x7b | Free tier available | Easy |
| **Cohere** | command-r-plus, command-r | Paid | Easy |

## Quick Start

### 1. Choose Your Provider

Edit your `.env` file and set the `LLM_PROVIDER`:

```bash
# Choose one: google, openai, anthropic, ollama, groq, cohere
LLM_PROVIDER=google
```

### 2. Set the Model (Optional)

Specify which model to use (or use the default):

```bash
# Model name - optional, uses provider defaults if not set
LLM_MODEL=gemini-2.0-flash-exp
```

### 3. Add Your API Key

Set the corresponding API key for your chosen provider.

---

## Provider-Specific Setup

### Google Gemini (Default)

**Best for:** Free tier users, fast responses, multimodal capabilities

**Setup:**
1. Get API key from: https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```bash
   LLM_PROVIDER=google
   LLM_MODEL=gemini-2.5-flash  # or gemini-2.5-flash, gemini-1.5-pro
   GOOGLE_API_KEY=your_api_key_here
   ```

**Available Models:**
- `gemini-2.0-flash-exp` - Latest experimental model (recommended)
- `gemini-2.5-flash` - Fast and efficient
- `gemini-1.5-pro` - Most capable, slower

**Cost:** Free tier available with generous limits

---

### OpenAI

**Best for:** High-quality responses, established API, wide model selection

**Setup:**
1. Install dependency:
   ```bash
   pip install langchain-openai
   ```
2. Get API key from: https://platform.openai.com/api-keys
3. Add to `.env`:
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4-turbo
   OPENAI_API_KEY=your_api_key_here
   ```

**Available Models:**
- `gpt-4o` - Latest GPT-4 Omni model
- `gpt-4o-mini` - Faster and cheaper variant (recommended)
- `gpt-4-turbo` - Previous generation

**Cost:** Pay per token - see [OpenAI Pricing](https://openai.com/pricing)

**Requirements.txt:**
```bash
# Uncomment in requirements.txt:
langchain-openai>=0.2.0
```

---

### Anthropic Claude

**Best for:** Long context windows, detailed analysis, safety features

**Setup:**
1. Install dependency:
   ```bash
   pip install langchain-anthropic
   ```
2. Get API key from: https://console.anthropic.com/
3. Add to `.env`:
   ```bash
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-5-sonnet-20241022  # or claude-3-opus-20240229
   ANTHROPIC_API_KEY=your_api_key_here
   ```

**Available Models:**
- `claude-3-5-sonnet-20241022` - Best balance (recommended)
- `claude-3-opus-20240229` - Most capable
- `claude-3-haiku-20240307` - Fastest and cheapest

**Cost:** Pay per token - see [Anthropic Pricing](https://www.anthropic.com/pricing)

**Requirements.txt:**
```bash
# Uncomment in requirements.txt:
langchain-anthropic>=0.3.0
```

---

### Ollama (Local Models)

**Best for:** Privacy, no API costs, offline usage, custom models

**Setup:**
1. Install Ollama: https://ollama.ai/download
2. Pull a model:
   ```bash
   ollama pull llama3.1
   ```
3. Start Ollama server:
   ```bash
   ollama serve
   ```
4. Install dependency:
   ```bash
   pip install langchain-ollama
   ```
5. Add to `.env`:
   ```bash
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.1  # or mistral, codellama, etc.
   OLLAMA_BASE_URL=http://localhost:11434  # default
   ```

**Available Models:**
- `llama3.1` - Meta's Llama 3.1 (recommended)
- `mistral` - Mistral AI's model
- `codellama` - Code-focused
- Many more at https://ollama.ai/library

**Cost:** Free (runs locally)

**Requirements:**
- Good GPU recommended for fast responses
- Sufficient RAM (8GB+ for 7B models)

**Requirements.txt:**
```bash
# Uncomment in requirements.txt:
langchain-ollama>=0.2.0
```

---

### Groq

**Best for:** Fast inference, free tier, cost-effective

**Setup:**
1. Install dependency:
   ```bash
   pip install langchain-groq
   ```
2. Get API key from: https://console.groq.com/
3. Add to `.env`:
   ```bash
   LLM_PROVIDER=groq
   LLM_MODEL=llama-3.3-70b-versatile  # or mixtral-8x7b-32768
   GROQ_API_KEY=your_api_key_here
   ```

**Available Models:**
- `llama-3.3-70b-versatile` - Latest Llama 3.3 (recommended)
- `mixtral-8x7b-32768` - Mixtral with large context
- `llama3-70b-8192` - Previous Llama 3

**Cost:** Free tier available with generous limits

**Requirements.txt:**
```bash
# Uncomment in requirements.txt:
langchain-groq>=0.2.0
```

---

### Cohere

**Best for:** Multilingual support, RAG applications

**Setup:**
1. Install dependency:
   ```bash
   pip install langchain-cohere
   ```
2. Get API key from: https://dashboard.cohere.com/api-keys
3. Add to `.env`:
   ```bash
   LLM_PROVIDER=cohere
   LLM_MODEL=command-r-plus  # or command-r
   COHERE_API_KEY=your_api_key_here
   ```

**Available Models:**
- `command-r-plus` - Most capable (recommended)
- `command-r` - Balanced performance
- `command` - Previous generation

**Cost:** Free trial, then pay per token

**Requirements.txt:**
```bash
# Uncomment in requirements.txt:
langchain-cohere>=0.3.0
```

---

## Switching Providers

To switch providers, simply update your `.env` file:

```bash
# Switch from Google to OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_key_here
```

Then restart the backend:
```bash
pkill -f "python -m api.main"
python -m api.main
```

No code changes needed!

---

## Testing Your Setup

### Check Current Configuration

The LLM provider is automatically initialized when you start the backend. Check the startup logs:

### Test the Chatbot

1. Analyze a product first (to populate Redis cache)
2. Ask a question via the chat endpoint
3. Check the response

If you see an error like "API key not found", verify your `.env` configuration.

---

## Comparison & Recommendations

### For Development (Free)
- **Recommended:** Google Gemini (`gemini-2.0-flash-exp`)
- **Alternative:** Groq (`llama-3.3-70b-versatile`)
- **Local:** Ollama (`llama3.1`)

### For Production
- **Best Quality:** OpenAI GPT-4o or Anthropic Claude 3.5 Sonnet
- **Best Value:** Google Gemini 2.5 Flash or Groq
- **Privacy-First:** Ollama (local deployment)

### Feature Comparison

| Feature | Google | OpenAI | Anthropic | Ollama | Groq | Cohere |
|---------|--------|--------|-----------|--------|------|--------|
| Free Tier | ✅ | ❌ | ❌ | ✅ | ✅ | Trial |
| Speed | Fast | Medium | Medium | Varies | Very Fast | Fast |
| Quality | Excellent | Excellent | Excellent | Good | Good | Good |
| Context Length | 128K+ | 128K | 200K | Varies | 32K+ | 128K |
| Privacy | Cloud | Cloud | Cloud | Local | Cloud | Cloud |

---

## Troubleshooting

### Error: "Unsupported LLM provider"

**Solution:** Check `LLM_PROVIDER` in `.env`. Valid values: `google`, `openai`, `anthropic`, `ollama`, `groq`, `cohere`

### Error: "API key not found"

**Solution:**
1. Verify the API key variable name matches your provider:
   - Google: `GOOGLE_API_KEY`
   - OpenAI: `OPENAI_API_KEY`
   - Anthropic: `ANTHROPIC_API_KEY`
   - Groq: `GROQ_API_KEY`
   - Cohere: `COHERE_API_KEY`
2. Restart the backend after updating `.env`

### Error: "Module not found: langchain_openai"

**Solution:** Install the provider-specific package:
```bash
pip install langchain-openai  # or langchain-anthropic, etc.
```

Or uncomment the line in `requirements.txt` and run:
```bash
pip install -r requirements.txt
```

### Ollama: Connection refused

**Solution:**
1. Check Ollama is running: `ollama list`
2. Start Ollama: `ollama serve`
3. Verify base URL in `.env`: `OLLAMA_BASE_URL=http://localhost:11434`

---

## Cost Optimization Tips

1. **Use Smaller Models:** Start with mini/flash variants (cheaper, faster)
2. **Set Lower Temperature:** Reduces token usage for factual tasks
3. **Cache Aggressively:** Enable Redis caching (24-hour TTL)
4. **Batch Requests:** Combine multiple questions in one chat session
5. **Try Free Tiers:** Google Gemini and Groq offer generous free tiers

---

## Environment Variables Reference

```bash
# LLM Configuration
LLM_PROVIDER=google  # google, openai, anthropic, ollama, groq, cohere
LLM_MODEL=gemini-2.0-flash-exp  # Optional, uses defaults if not set

# API Keys (set only for your chosen provider)
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
COHERE_API_KEY=your_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Other Services
SERPER_API_KEY=your_serper_key_here  # For price comparison & web search
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Need Help?

- Check the example `.env.example` file
- Review the main README.md
- Open an issue on GitHub
- Check provider documentation links above

---

## License

This configuration system is part of the Amazon Product Analysis Agent and follows the same license.
