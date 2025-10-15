# Amazon Product Analysis Agent - Frontend

Modern React TypeScript frontend for the Amazon Product Analysis Agent.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **React Context** - State management
- **React Markdown** - Markdown rendering

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── tabs/           # Tab components
│   │   │   ├── AnalysisTab.tsx
│   │   │   ├── ReviewsTab.tsx
│   │   │   └── ChatTab.tsx
│   │   ├── Header.tsx
│   │   ├── ScrapeForm.tsx
│   │   └── ProductDetails.tsx
│   │
│   ├── contexts/           # State management
│   │   └── ProductContext.tsx
│   │
│   ├── services/           # API services
│   │   └── api.ts
│   │
│   ├── types/              # TypeScript types
│   │   └── index.ts
│   │
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
│
├── public/                 # Static assets
├── .env.development        # Development environment
├── .env.production         # Production environment
├── .env.local.example      # Local environment template
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript config
└── vite.config.ts          # Vite config
```

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running (see ../backend/README.md)

### Installation

```bash
# Install dependencies
npm install

# Copy environment template (optional)
cp .env.local.example .env.local

# Start development server
npm run dev
```

The app will be available at http://localhost:5000

## Environment Configuration

### Development (.env.development)

Used automatically when running `npm run dev`:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG=true
VITE_API_TIMEOUT=120000
```

### Production (.env.production)

Used automatically when running `npm run build`:

```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_DEBUG=false
VITE_API_TIMEOUT=120000
```

### Local Overrides (.env.local)

Create `.env.local` for local development overrides. This file is gitignored and takes precedence:

```bash
cp .env.local.example .env.local
# Edit .env.local with your custom values
```

**Priority Order:**
1. `.env.local` (highest priority, gitignored)
2. `.env.development` or `.env.production` (based on mode)
3. `.env` (defaults)

## Available Scripts

### Development

```bash
# Start dev server with hot reload
npm run dev

# Start dev server on different port (default is 5000)
npm run dev -- --port 3000
```

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Type Checking & Linting

```bash
# Type check
npm run tsc

# Lint code
npm run lint
```

## API Integration

The frontend communicates with the backend API via the API client (`src/services/api.ts`).

### API Client Configuration

```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

### Available Endpoints

**Products:**
- `POST /api/v1/products/scrape` - Scrape Amazon product
- `POST /api/v1/products/analyze` - Analyze product
- `GET /api/v1/products/product/{asin}` - Get cached product

**Chat:**
- `POST /api/v1/chat/ask` - Ask question
- `GET /api/v1/chat/history/{session_id}` - Get history
- `POST /api/v1/chat/clear` - Clear history

## Features

### 1. Product Scraping
- Enter Amazon product URL
- Automatic product data extraction
- Display product details, features, reviews

### 2. AI Analysis
- One-click product analysis
- LLM-powered insights
- Price comparison
- External reviews integration

### 3. Reviews Tab
- Amazon reviews with filters
- External tech reviews
- Comparison articles
- Sentiment summary

### 4. Interactive Chat
- Ask questions about products
- Context-aware responses
- Rich link formatting
- Persistent chat history

## Component Architecture

### State Management (Context)

Global state managed via React Context (`ProductContext`):

```typescript
interface ProductContextType {
  productData: ProductData | null;
  analysis: string | null;
  sessionId: string;
  chatHistory: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  // ... methods
}
```

### Type Safety

All API models are typed in `src/types/index.ts`:

```typescript
interface ProductData {
  asin: string;
  title: string;
  price?: string;
  reviews: Review[];
  // ...
}
```

## Styling

Currently using inline styles with a consistent design system:

- **Primary Color:** #ff9900 (Amazon orange)
- **Dark:** #232f3e (Amazon navy)
- **Light:** #f5f5f5 (Background)

### Future: CSS Modules or Styled Components

Consider migrating to:
- CSS Modules for scoped styles
- Styled Components for dynamic styling
- Tailwind CSS for utility-first approach

## Development Tips

### Hot Module Replacement (HMR)

Vite provides fast HMR. Changes are reflected instantly without full page reload.

### TypeScript Strict Mode

The project uses strict TypeScript checking. Ensure all types are properly defined.

### API Error Handling

The API client includes automatic error handling:

```typescript
client.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);
```

### Debug Mode

Enable debug logging via environment:

```bash
VITE_DEBUG=true npm run dev
```

## Testing

### Unit Tests (Future)

```bash
# Run tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage
```

### E2E Tests (Future)

Consider adding Playwright or Cypress for end-to-end testing.

## Deployment

### Build for Production

```bash
npm run build
```

Output: `dist/` directory with optimized static files.

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Deploy to AWS S3 + CloudFront

```bash
npm run build
aws s3 sync dist/ s3://your-bucket-name
```

### Environment Variables for Deployment

Set `VITE_API_BASE_URL` to your production backend URL in your deployment platform:

- Vercel: Project Settings → Environment Variables
- Netlify: Site Settings → Build & Deploy → Environment
- AWS: Update CloudFormation/CDK configuration

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Lazy loading for components
- Code splitting with Vite
- Optimized production builds
- Gzip compression (server-side)

## Troubleshooting

### Port Already in Use

```bash
npm run dev -- --port 3000  # Use a different port
```

### API Connection Error

- Check backend is running: http://localhost:8000/health
- Verify `VITE_API_BASE_URL` in environment
- Check CORS settings in backend

### TypeScript Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Fails

```bash
# Check TypeScript errors
npm run tsc

# Clear Vite cache
rm -rf node_modules/.vite
npm run build
```

## Contributing

1. Create feature branch
2. Make changes
3. Test locally
4. Submit pull request

## License

MIT License - See main project README
