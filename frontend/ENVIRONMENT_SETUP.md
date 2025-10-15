# Frontend Environment Configuration Guide

This guide explains how to configure environment variables for different deployment scenarios.

## Environment Files Overview

The frontend uses Vite's environment variable system with the following files:

| File | Purpose | Tracked in Git | Used When |
|------|---------|---------------|-----------|
| `.env.development` | Development defaults | ✅ Yes | `npm run dev` |
| `.env.production` | Production defaults | ✅ Yes | `npm run build` |
| `.env.local` | Local overrides | ❌ No | Always (highest priority) |
| `.env.local.example` | Local template | ✅ Yes | Template for .env.local |
| `.env.example` | General template | ✅ Yes | Documentation |

## Priority Order

Vite loads environment variables in this order (highest to lowest priority):

1. `.env.local` (local overrides, gitignored)
2. `.env.[mode]` (`.env.development` or `.env.production`)
3. `.env` (base defaults)

## Environment Variables

### VITE_API_BASE_URL

The backend API base URL.

**Development:**
```bash
VITE_API_BASE_URL=http://localhost:8000
```

**Production:**
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

**Important:** All environment variables exposed to the client must start with `VITE_` prefix.

### VITE_DEBUG

Enable/disable debug logging.

```bash
VITE_DEBUG=true   # Development
VITE_DEBUG=false  # Production
```

### VITE_API_TIMEOUT

API request timeout in milliseconds.

```bash
VITE_API_TIMEOUT=120000  # 2 minutes (for long scraping operations)
```

## Setup for Different Scenarios

### 1. Local Development (Default)

Use the pre-configured `.env.development`:

```bash
npm run dev
```

No additional setup needed! Automatically connects to `http://localhost:8000`.

### 2. Local Development (Custom Backend URL)

Create `.env.local` to override:

```bash
# Copy template
cp .env.local.example .env.local

# Edit .env.local
VITE_API_BASE_URL=http://192.168.1.100:8000  # Your custom backend URL
VITE_DEBUG=true
```

Then run:
```bash
npm run dev
```

### 3. Testing Production Build Locally

Build with production config but override API URL:

```bash
# Create .env.local
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Build
npm run build

# Preview
npm run preview
```

### 4. Production Deployment

Update `.env.production` with your production backend URL:

```bash
VITE_API_BASE_URL=https://api.yourproductiondomain.com
VITE_DEBUG=false
VITE_API_TIMEOUT=120000
```

Then build:
```bash
npm run build
```

## Deployment Platform Setup

### Vercel

1. Go to Project Settings → Environment Variables
2. Add variables:
   - `VITE_API_BASE_URL` = `https://your-backend-url.com`
3. Select environment: Production, Preview, or Development
4. Deploy

**Note:** Vercel automatically uses `.env.production` during build.

### Netlify

1. Go to Site Settings → Build & Deploy → Environment
2. Add variables:
   - `VITE_API_BASE_URL` = `https://your-backend-url.com`
3. Deploy

### AWS Amplify

1. Go to App Settings → Environment Variables
2. Add:
   - `VITE_API_BASE_URL` = `https://your-backend-url.com`
3. Save and redeploy

### Docker

Create a Dockerfile with build args:

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# Build with environment variables
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build:
```bash
docker build \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com \
  -t amazon-analysis-frontend .
```

## Environment Variable Access in Code

### Correct Way

```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const DEBUG = import.meta.env.VITE_DEBUG === 'true';
```

### Type Safety

Create `src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_DEBUG: string;
  readonly VITE_API_TIMEOUT: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

## Security Best Practices

### ✅ DO:
- Use `VITE_` prefix for all client-exposed variables
- Keep production URLs in `.env.production`
- Document all environment variables
- Use `.env.local` for sensitive local config
- Add `.env.local` to `.gitignore`

### ❌ DON'T:
- Commit `.env.local` to git
- Store API keys or secrets in environment variables (they're exposed to client)
- Use environment variables without the `VITE_` prefix
- Hardcode URLs in source code

## Troubleshooting

### Environment Variables Not Loading

**Problem:** Changes to `.env` files not reflected

**Solution:**
```bash
# Restart dev server
# Kill with Ctrl+C, then:
npm run dev
```

Vite only loads env files on startup.

### Wrong Backend URL

**Problem:** API calls going to wrong URL

**Solution:**
```bash
# Check current value
console.log(import.meta.env.VITE_API_BASE_URL)

# Check all loaded env files
cat .env.local .env.development .env.production

# Remove conflicting .env.local
rm .env.local

# Restart dev server
npm run dev
```

### Production Build Issues

**Problem:** Environment variables not working in production build

**Solution:**
```bash
# Check build output
npm run build

# Test locally
npm run preview

# Verify API URL is baked into bundle
grep -r "VITE_API_BASE_URL" dist/
```

### CORS Errors

**Problem:** API requests blocked by CORS

**Solution:**

1. Check backend CORS configuration allows frontend URL
2. Verify `VITE_API_BASE_URL` is correct
3. Check browser console for exact error
4. For local dev, backend should allow `http://localhost:5000`

## Testing Environment Configuration

### Verify Current Environment

Create a test component:

```typescript
// src/components/EnvTest.tsx
export const EnvTest = () => {
  return (
    <div>
      <h3>Environment Variables</h3>
      <pre>
        {JSON.stringify({
          API_URL: import.meta.env.VITE_API_BASE_URL,
          DEBUG: import.meta.env.VITE_DEBUG,
          MODE: import.meta.env.MODE,
          DEV: import.meta.env.DEV,
          PROD: import.meta.env.PROD,
        }, null, 2)}
      </pre>
    </div>
  );
};
```

Add to your app temporarily to verify configuration.

## Examples

### Example 1: Local Development with Remote Backend

```bash
# .env.local
VITE_API_BASE_URL=https://staging-api.yourcompany.com
VITE_DEBUG=true
```

### Example 2: Multiple Environments

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000

# .env.staging (create custom)
VITE_API_BASE_URL=https://staging-api.yourcompany.com

# .env.production
VITE_API_BASE_URL=https://api.yourcompany.com
```

Build for staging:
```bash
npm run build -- --mode staging
```

### Example 3: Local Network Testing

```bash
# .env.local
VITE_API_BASE_URL=http://192.168.1.100:8000  # Your machine's IP
```

Access from phone/tablet on same network:
```
http://192.168.1.100:3000  (replace with your machine's IP)
```

## Quick Reference

| Scenario | File to Use | Command |
|----------|-------------|---------|
| Local dev (default backend) | `.env.development` | `npm run dev` |
| Local dev (custom backend) | `.env.local` | `npm run dev` |
| Production build | `.env.production` | `npm run build` |
| Preview prod build | `.env.local` + `.env.production` | `npm run preview` |
| Custom environment | `.env.[mode]` | `npm run build -- --mode [mode]` |

## Support

For issues with environment configuration:

1. Check this guide
2. Verify file names (`.env.development` not `.env.dev`)
3. Restart dev server after changes
4. Check browser console for loaded values
5. Review Vite documentation: https://vitejs.dev/guide/env-and-mode.html
