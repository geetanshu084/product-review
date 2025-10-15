   # Project Structure

This document shows the complete directory structure of the Amazon Product Analysis Agent project after the backend/frontend reorganization.

## Root Directory

```
amazon-review/
├── backend/                    # Python backend (Streamlit + core logic)
├── frontend/                   # React TypeScript frontend
├── README.md                   # Main project documentation
├── README_ARCHITECTURE.md      # Architecture details
├── SETUP.md                    # Setup guide
├── PROJECT_STRUCTURE.md        # This file
└── .gitignore                  # Git ignore rules
```

## Backend Directory

```
backend/
├── src/                        # Core Python source code
│   ├── scraper.py             # Amazon product scraper
│   ├── analyzer.py            # Product analyzer with LLM
│   ├── chatbot.py             # LangChain chatbot
│   └── analysis/
│       ├── __init__.py
│       ├── price_comparison.py  # Multi-platform price comparison
│       └── web_search.py        # External review aggregation
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_scraper.py
│   ├── test_analysis.py
│   ├── test_caching.py
│   ├── test_pagination.py
│   ├── test_price_comparison.py
│   ├── test_price_comparison_qa.py
│   ├── test_product_details.py
│   ├── test_qna_comprehensive.py
│   ├── test_langchain_tool_search.py
│   └── test_web_search.py
│
├── config/                     # Configuration files
│   └── prompts/
│       ├── agent_prompt.txt           # Chatbot system prompt
│       └── product_analysis_prompt.txt # Analysis prompt
│
├── docs/                       # Documentation
│   ├── PRICE_COMPARISON.md
│   ├── WEB_SEARCH_QA.md
│   └── GCP_SETUP_GUIDE.md
│
├── utils/                      # Utility functions
│   └── __init__.py
│
├── app.py                      # Main Streamlit application
├── example_usage.py            # Usage examples
├── verify_setup.py             # Setup verification script
├── requirements.txt            # Python dependencies
├── README.md                   # Backend documentation
├── QUICKSTART.md              # Quick start guide
├── CLAUDE.md                  # Claude AI guidance
├── req2.md                    # Feature requirements (Phase 2)
├── requirement.md             # Initial requirements
├── llm_extracted_data.json    # Test data
├── test_product_data.json     # Test data
├── .env                       # Environment variables
└── .env.example               # Environment template
```

## Frontend Directory

```
frontend/
├── src/
│   ├── components/            # React components
│   │   ├── tabs/
│   │   │   ├── AnalysisTab.tsx
│   │   │   ├── ReviewsTab.tsx
│   │   │   └── ChatTab.tsx
│   │   ├── Header.tsx
│   │   ├── ScrapeForm.tsx
│   │   └── ProductDetails.tsx
│   │
│   ├── contexts/              # React Context (state management)
│   │   └── ProductContext.tsx
│   │
│   ├── services/              # API services
│   │   └── api.ts            # Axios API client
│   │
│   ├── types/                 # TypeScript types
│   │   └── index.ts
│   │
│   ├── hooks/                 # Custom React hooks (if needed)
│   ├── pages/                 # Page components (if needed)
│   │
│   ├── App.tsx                # Main application component
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
│
├── public/                    # Public assets
├── node_modules/              # NPM dependencies (not in git)
├── package.json               # NPM dependencies and scripts
├── package-lock.json          # Locked versions
├── tsconfig.json              # TypeScript configuration
├── tsconfig.node.json         # TypeScript config for Node
├── vite.config.ts             # Vite build configuration
├── index.html                 # HTML entry point
├── .env                       # Environment variables (not in git)
├── .env.example               # Environment template
└── README.md                  # Frontend documentation (if created)
```

## Key Files by Purpose

### Backend Core Logic
- `backend/src/scraper.py` - Web scraping functionality
- `backend/src/analyzer.py` - AI analysis engine
- `backend/src/chatbot.py` - Conversational AI
- `backend/src/analysis/price_comparison.py` - Price comparison
- `backend/src/analysis/web_search.py` - External reviews

### Backend Application
- `backend/app.py` - Streamlit web application
- `backend/example_usage.py` - Code examples
- `backend/verify_setup.py` - Environment verification

### Frontend Core
- `frontend/src/App.tsx` - Main React app
- `frontend/src/contexts/ProductContext.tsx` - State management
- `frontend/src/services/api.ts` - API client
- `frontend/src/types/index.ts` - TypeScript definitions

### Configuration
- `backend/config/prompts/` - LLM prompt templates
- `backend/.env` - Backend environment variables
- `frontend/.env` - Frontend environment variables
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node dependencies

### Documentation
- `README.md` - Main project overview
- `README_ARCHITECTURE.md` - Architecture documentation
- `SETUP.md` - Setup instructions
- `PROJECT_STRUCTURE.md` - This file
- `backend/README.md` - Backend-specific docs
- `backend/docs/` - Feature documentation

### Testing
- `backend/tests/` - All test files
- `backend/test_*.json` - Test data files

## Directory Organization Principles

### Backend
- **src/** - All production Python code
- **tests/** - All test files separate from source
- **config/** - Configuration and templates
- **docs/** - Documentation specific to backend features
- Root level - Application entry points and utilities

### Frontend
- **src/components/** - Reusable UI components
- **src/contexts/** - Global state management
- **src/services/** - API and external services
- **src/types/** - TypeScript type definitions
- Root level - Configuration and entry point

## Running the Application

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Git Ignored Files

The following are not tracked in git:
- `venv/` - Python virtual environment
- `backend/__pycache__/` - Python cache
- `backend/.env` - Backend secrets
- `frontend/node_modules/` - NPM packages
- `frontend/dist/` - Build output
- `frontend/.env` - Frontend secrets
- `.DS_Store` - macOS files
- `.idea/` - IDE files

## Clean Architecture Benefits

1. **Separation of Concerns**
   - Backend contains all Python logic
   - Frontend contains all React code
   - No mixing of technologies

2. **Independent Development**
   - Backend can be developed/tested independently
   - Frontend can be developed/tested independently
   - Different teams can work simultaneously

3. **Clear Dependencies**
   - Backend: requirements.txt
   - Frontend: package.json
   - No confusion about what goes where

4. **Easy Deployment**
   - Backend can be deployed separately (e.g., to cloud functions)
   - Frontend can be deployed separately (e.g., to CDN)
   - Microservices-ready architecture

5. **Better Version Control**
   - Backend changes don't trigger frontend rebuilds
   - Frontend changes don't require backend restarts
   - Clear commit history

## Migration Notes

This structure was created by:
1. Creating `backend/` directory
2. Moving all Python code from root to `backend/`
3. Moving tests, config, utils to `backend/`
4. Moving documentation files to `backend/`
5. Keeping `frontend/` in place
6. Updating README files to reflect new structure

The application functionality remains the same, only the organization has changed.
