# Frontend Documentation

Modern React TypeScript frontend for the Product Analysis Agent with real-time updates, rich markdown rendering, and conversational chat interface.

## Tech Stack

### Core Technologies

- **React 18** - UI framework with concurrent rendering
- **TypeScript** - Static type checking and enhanced IDE support
- **Vite** - Next-generation frontend build tool with HMR
- **React Router v6** - Client-side routing (if using multi-page)

### Libraries

- **Axios** - Promise-based HTTP client with interceptors
- **TanStack Query (React Query)** - Server state management and caching
- **React Context API** - Global state management
- **react-markdown** - Markdown rendering with custom components

### Styling

- **CSS-in-JS** - Inline styles with TypeScript objects
- **Responsive Design** - Mobile-first approach
- **Color Palette**: Amazon-inspired (#ff9900, #232f3e)

## Project Structure

```
frontend/
├── src/
│   ├── components/              # React components
│   │   ├── tabs/                # Tab-based views
│   │   │   ├── AnalysisTab.tsx  # Product analysis display
│   │   │   ├── ReviewsTab.tsx   # Reviews with filters
│   │   │   └── ChatTab.tsx      # Interactive Q&A chat
│   │   ├── ProductAnalysisView.tsx  # Main analysis component
│   │   ├── Header.tsx           # Application header
│   │   ├── ScrapeForm.tsx       # URL input form
│   │   └── ProductDetails.tsx   # Product info display
│   │
│   ├── contexts/                # React Context providers
│   │   └── ProductContext.tsx   # Global product state
│   │
│   ├── services/                # API and external services
│   │   └── api.ts               # Axios client and API methods
│   │
│   ├── types/                   # TypeScript type definitions
│   │   └── index.ts             # All interfaces and types
│   │
│   ├── App.tsx                  # Root component with routing
│   ├── main.tsx                 # React DOM entry point
│   └── index.css                # Global CSS styles
│
├── public/                      # Static assets
│   ├── vite.svg                 # Vite logo
│   └── ...                      # Other static files
│
├── .env.development             # Development environment
├── .env.production              # Production environment
├── .env.local.example           # Local environment template
├── package.json                 # Dependencies and scripts
├── tsconfig.json                # TypeScript configuration
├── vite.config.ts               # Vite build configuration
└── index.html                   # HTML entry point
```

## Architecture Overview

### Data Flow

```
User Input → Component → ProductContext → API Service → Backend
                ↓                              ↓
            UI Update  ←  State Update  ←  Response
```

### Component Hierarchy

```
App
├── ProductContext.Provider
    ├── Header
    ├── ScrapeForm
    ├── ProductAnalysisView
    │   ├── Image Gallery
    │   ├── Product Info
    │   ├── Price Display
    │   └── ReactMarkdown (Analysis)
    └── Tabs
        ├── AnalysisTab
        ├── ReviewsTab (with sub-tabs)
        │   ├── Platform Reviews
        │   ├── External Content
        │   └── Summary
        └── ChatTab
            ├── Message List
            └── Input Form
```

## Core Components

### 1. ProductContext (`src/contexts/ProductContext.tsx`)

Global state management using React Context API:

**State Structure:**
```typescript
interface ProductContextType {
  productData: ProductData | null;      // Scraped product data
  analysis: string | null;              // LLM-generated analysis
  sessionId: string;                    // Unique session identifier
  chatHistory: ChatMessage[];           // Chat conversation history
  isLoading: boolean;                   // Loading state
  error: string | null;                 // Error messages

  // Actions
  scrapeAndAnalyze: (url: string, options?: ScrapeOptions) => Promise<void>;
  askQuestion: (question: string) => Promise<void>;
  clearChat: () => Promise<void>;
  resetState: () => void;
}
```

**Key Features:**
- Session ID generation with UUID
- Persistent state across component remounts
- Error handling with user-friendly messages
- Loading state management for async operations

### 2. ProductAnalysisView (`src/components/ProductAnalysisView.tsx`)

Main component displaying comprehensive product analysis:

**Features:**
- Image gallery with navigation (previous/next buttons)
- Platform-dynamic headers (Amazon 🛒 / Flipkart 🛍️)
- Price display with competitor filtering
- Bank offers with expandable sections
- Rich markdown rendering with custom components
- Text wrapping for long content

**Custom ReactMarkdown Renderers:**
```typescript
<ReactMarkdown
  components={{
    p: ({children}) => <p style={{...wrappingStyles}}>{children}</p>,
    pre: ({children}) => <pre style={{...codeBlockStyles}}>{children}</pre>,
    code: ({children}) => <code style={{...inlineCodeStyles}}>{children}</code>,
  }}
>
  {analysis}
</ReactMarkdown>
```

**Dynamic Platform Detection:**
```typescript
const platformName = product.platform || 'Amazon';
const platformIcon = platformName === 'Flipkart' ? '🛍️' : '🛒';
```

### 3. ReviewsTab (`src/components/tabs/ReviewsTab.tsx`)

Multi-view reviews component with filtering:

**Sub-Tabs:**
1. **Platform Reviews** (Amazon/Flipkart)
   - Rating filter (1-5 stars)
   - Verified purchase filter
   - Review cards with rating, title, text, date

2. **External Content** (Merged view)
   - External reviews (tech blogs)
   - Comparison articles
   - Reddit discussions
   - News articles
   - Badge-based categorization

3. **Summary**
   - Key findings (bullet points)
   - Red flags (warning indicators)
   - Overall sentiment analysis

**Platform-Dynamic Features:**
```typescript
const platformReviews = productData.reviews || [];
const mergedExternalContent = [
  ...externalReviews.map(r => ({ ...r, type: 'review' })),
  ...comparisonArticles.map(c => ({ ...c, type: 'comparison' })),
  ...redditDiscussions.map(rd => ({ ...rd, type: 'reddit' })),
  ...newsArticles.map(na => ({ ...na, type: 'news' }))
];
```

### 4. ChatTab (`src/components/tabs/ChatTab.tsx`)

Interactive Q&A interface with rich link formatting:

**Features:**
- Message history display (user + assistant)
- Input form with Enter key support
- Auto-scroll to latest message
- Rich link rendering for product recommendations
- Loading states with visual feedback
- Clear chat functionality

**Rich Link Formatting:**
```typescript
// Detects product recommendation links in format:
// "Product Name - Platform - Price - [Link](url)"
const formatMessage = (content: string) => {
  // Regex pattern for rich links
  // Renders as styled cards instead of plain text
}
```

**Chat Input Handling:**
```typescript
const handleAsk = async (e: React.FormEvent) => {
  e.preventDefault();
  if (!question.trim() || isLoading) return;

  await askQuestion(question);
  setQuestion('');  // Clear input after sending
  scrollToBottom();  // Auto-scroll to new message
};
```

### 5. ScrapeForm (`src/components/ScrapeForm.tsx`)

URL input form with analysis options:

**Fields:**
- Product URL input (Amazon/Flipkart)
- Include Price Comparison checkbox
- Include External Reviews checkbox

**Validation:**
- URL format validation
- Platform detection (Amazon/Flipkart)
- Error display for invalid URLs

### 6. API Service (`src/services/api.ts`)

Axios-based HTTP client with centralized configuration:

**Configuration:**
```typescript
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 120000,  // 2 minutes for long analysis
  headers: {
    'Content-Type': 'application/json',
  },
});
```

**API Methods:**
```typescript
// Products
scrapeAndAnalyzeProduct(url: string, options?: ScrapeOptions): Promise<ProductResponse>
getProduct(productId: string): Promise<ProductData>

// Chat
askQuestion(sessionId: string, productId: string, question: string): Promise<ChatResponse>
getChatHistory(sessionId: string): Promise<ChatMessage[]>
clearChat(sessionId: string): Promise<void>
```

**Error Handling:**
```typescript
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message;
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);
```

## Type System

### Core Types (`src/types/index.ts`)

**Product Data:**
```typescript
interface ProductData {
  asin: string;
  title: string;
  platform?: string;              // 'Amazon' | 'Flipkart'
  brand?: string;
  price?: string;
  rating?: string;
  ratings_count?: string;
  features?: string[];
  description?: string;
  specifications?: Record<string, string>;
  images?: string[];
  reviews: Review[];
  bank_offers?: BankOffer[];
  price_comparison?: PriceComparison;
  web_search_analysis?: WebSearchAnalysis;
}
```

**Review Structure:**
```typescript
interface Review {
  rating: string;                 // e.g., "4.0 out of 5 stars"
  title: string;
  text: string;
  date: string;
  verified_purchase: boolean;
  helpful_votes?: number;
}
```

**Web Search Analysis:**
```typescript
interface WebSearchAnalysis {
  external_reviews: ExternalReview[];
  comparison_articles: ComparisonArticle[];
  reddit_discussions: RedditDiscussion[];
  news_articles: NewsArticle[];
  video_reviews: VideoReview[];
  key_findings: string[];
  red_flags: string[];
  overall_sentiment: {
    sentiment: string;            // 'Positive' | 'Negative' | 'Mixed'
    confidence: string;           // 'High' | 'Medium' | 'Low'
    summary: string;
  };
}
```

**Chat Types:**
```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatRequest {
  session_id: string;
  product_id: string;
  question: string;
}
```

## Styling Approach

### CSS-in-JS Pattern

The application uses inline styles with TypeScript objects for type safety and component encapsulation:

**Style Object Pattern:**
```typescript
const styles = {
  container: {
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  button: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};

// Usage
<div style={styles.container}>
  <button style={styles.button}>Click Me</button>
</div>
```

### Design System

**Color Palette:**
- Primary: `#ff9900` (Amazon Orange)
- Dark: `#232f3e` (Amazon Navy)
- Light Gray: `#f5f5f5` (Background)
- Border: `#e0e0e0`
- Success: `#00a814` (Verified)
- Warning: `#d32f2f` (Red flags)

**Typography:**
- Base font: System fonts
- Monospace: For code blocks
- Font sizes: 0.75rem - 1.5rem

**Spacing Scale:**
- 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem, 3rem

### Text Wrapping Solution

For handling long text in analysis section:

```typescript
const wrappingStyles = {
  wordWrap: 'break-word' as const,
  overflowWrap: 'anywhere' as const,
  wordBreak: 'break-word' as const,
  whiteSpace: 'pre-wrap' as const,
  maxWidth: '100%',
};
```

## Configuration

### Environment Variables

**Development (`.env.development`):**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG=true
VITE_API_TIMEOUT=120000
```

**Production (`.env.production`):**
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_DEBUG=false
VITE_API_TIMEOUT=120000
```

**Local Overrides (`.env.local`):**
```bash
cp .env.local.example .env.local
# Edit with your custom values
```

**Environment Priority:**
1. `.env.local` (highest, gitignored)
2. `.env.development` / `.env.production` (mode-specific)
3. `.env` (defaults)

### Vite Configuration (`vite.config.ts`)

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

## Development

### Setup

```bash
# Install dependencies
npm install

# Copy environment template (optional)
cp .env.local.example .env.local

# Start development server
npm run dev
```

The app will be available at http://localhost:5000 (or next available port if 5000 is in use).

### Available Scripts

```bash
# Development
npm run dev              # Start dev server with HMR
npm run dev -- --port 3000  # Use custom port

# Production Build
npm run build            # Build for production
npm run preview          # Preview production build

# Type Checking & Linting
npm run tsc              # TypeScript type check
npm run lint             # ESLint code check
```

### Hot Module Replacement (HMR)

Vite provides instant HMR:
- Component changes reflect immediately
- State preserved across updates
- No full page reload needed

### Development Tips

**1. TypeScript Strict Mode:**
- Use proper type annotations
- Avoid `any` type
- Enable strict null checks

**2. Component Organization:**
- Keep components focused (single responsibility)
- Extract reusable logic to hooks
- Use TypeScript interfaces for props

**3. State Management:**
- Use Context for global state
- Keep local state in components
- Consider React Query for server state

**4. Performance:**
- Use `React.memo()` for expensive components
- Lazy load routes and heavy components
- Optimize images (WebP format)

## Testing

### Unit Tests (Future Enhancement)

```bash
# Install testing dependencies
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Run tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

### E2E Tests (Future Enhancement)

Consider Playwright or Cypress:

```bash
# Playwright
npm install -D @playwright/test
npx playwright test

# Cypress
npm install -D cypress
npx cypress open
```

## Deployment

### Build for Production

```bash
npm run build
```

Output: `dist/` directory with optimized static files.

### Deployment Platforms

#### Vercel

```bash
npm install -g vercel
vercel
```

Set environment variable:
- `VITE_API_BASE_URL` → Your production backend URL

#### Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

Configuration in `netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

#### AWS S3 + CloudFront

```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

#### Docker

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t product-analysis-frontend .
docker run -p 80:80 product-analysis-frontend
```

## Troubleshooting

### Port Already in Use

```bash
# Use different port
npm run dev -- --port 3000

# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### API Connection Error

1. Check backend is running: `http://localhost:8000/health`
2. Verify `VITE_API_BASE_URL` in environment
3. Check CORS settings in backend
4. Inspect browser console for errors

### TypeScript Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Type check
npm run tsc
```

### Build Fails

```bash
# Check TypeScript errors
npm run tsc

# Clear Vite cache
rm -rf node_modules/.vite

# Clean build
npm run build
```

### CORS Errors

Ensure backend allows your frontend origin:
- Development: `http://localhost:5000`
- Check `BACKEND_CORS_ORIGINS` in backend config

### Text Overflow Issues

If text is cut off:
1. Check parent container width
2. Apply wrapping styles
3. Use custom ReactMarkdown renderers
4. Test with long content

## Performance Optimization

### Code Splitting

Vite automatically splits code by route:

```typescript
import { lazy, Suspense } from 'react';

const AnalysisTab = lazy(() => import('./components/tabs/AnalysisTab'));

<Suspense fallback={<div>Loading...</div>}>
  <AnalysisTab />
</Suspense>
```

### Image Optimization

```typescript
// Use WebP format with fallback
<picture>
  <source srcSet={webpImage} type="image/webp" />
  <img src={jpgImage} alt="Product" />
</picture>
```

### Bundle Analysis

```bash
npm run build
npx vite-bundle-visualizer
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Android)

## Future Enhancements

1. **Testing Suite** - Add Vitest + Testing Library
2. **CSS Framework** - Migrate to Tailwind CSS or Styled Components
3. **State Management** - Consider Zustand or Jotai for complex state
4. **Progressive Web App** - Add service worker and offline support
5. **Accessibility** - Improve ARIA labels and keyboard navigation
6. **Internationalization** - Add i18n support for multiple languages
7. **Dark Mode** - Theme switching with system preference detection
8. **Animation** - Add Framer Motion for smooth transitions

## Contributing

1. Create feature branch from `main`
2. Follow existing code style and patterns
3. Add types for all new components
4. Test locally before submitting PR
5. Update documentation as needed
