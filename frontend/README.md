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


## Configuration

### Environment Variables

The application uses two environment profiles:

**Local Development (`.env.local`):**

Create this file from the template for local development:
```bash
cp .env.local.example .env.local
# Edit with your custom values
```

Default values (from `.env.local.example`):
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG=true
VITE_API_TIMEOUT=120000
```

**Production (`.env.production`):**

Used automatically when building for production:
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_DEBUG=false
VITE_API_TIMEOUT=120000
```

**Environment Priority:**
1. `.env.local` (highest priority, gitignored, used for local development)
2. `.env.production` (used when running `npm run build`)
3. `.env` (defaults, if exists)

### Vite Configuration (`vite.config.ts`)

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
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

The app will be available at http://localhost:3000 (or next available port if 3000 is in use).

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
- Development: `http://localhost:3000`
- Check `BACKEND_CORS_ORIGINS` in backend config


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
