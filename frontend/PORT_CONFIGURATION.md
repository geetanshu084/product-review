# Frontend Port Configuration

## Port Settings

The frontend is configured to run on **port 5000** by default.

## Configuration Files

### 1. Vite Configuration (`vite.config.ts`)

```typescript
export default defineConfig({
  // ...
  server: {
    port: 5000,  // Development server port
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // Backend API
        changeOrigin: true,
      },
    },
  },
})
```

### 2. Package Scripts (`package.json`)

```json
{
  "scripts": {
    "dev": "vite",              // Starts on port 5000 (from vite.config.ts)
    "preview": "vite preview --port 5000"  // Preview also on 5000
  }
}
```

## Access Points

| Mode | Command | URL | Description |
|------|---------|-----|-------------|
| Development | `npm run dev` | http://localhost:5000 | Hot reload dev server |
| Preview | `npm run preview` | http://localhost:5000 | Preview production build |
| Backend API | - | http://localhost:8000 | Backend Streamlit app |

## Changing the Port

### Temporary Change (Single Session)

```bash
# Start on a different port
npm run dev -- --port 3000

# Or set via environment variable
PORT=3000 npm run dev
```

### Permanent Change

Edit `vite.config.ts`:

```typescript
server: {
  port: 3000,  // Change to your desired port
  // ...
}
```

And update `package.json`:

```json
"preview": "vite preview --port 3000"
```

## CORS Configuration

If you change the frontend port, ensure the backend allows the new origin.

### For Streamlit Backend

Streamlit automatically handles CORS. No additional configuration needed.

### For FastAPI Backend (Future)

Update backend CORS settings to include the new frontend URL:

```python
# backend/app/main.py
BACKEND_CORS_ORIGINS = [
    "http://localhost:5000",  # Frontend dev server
    "http://localhost:3000",  # Alternative port
    # Add production URLs
]
```

## Network Access

### Access from Other Devices

Start with host binding:

```bash
npm run dev -- --host
```

Then access from other devices on the same network:

```
http://[YOUR_IP]:5000
```

Find your IP:
```bash
# macOS/Linux
ifconfig | grep "inet "

# Windows
ipconfig
```

### Mobile Testing

1. Find your computer's IP address (e.g., 192.168.1.100)
2. Start dev server: `npm run dev -- --host`
3. Access from mobile: `http://192.168.1.100:5000`

**Note:** Ensure your firewall allows connections on port 5000.

## Port Conflicts

### Error: Port 5000 Already in Use

**Option 1: Kill the process using port 5000**

```bash
# macOS/Linux
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Option 2: Use a different port**

```bash
npm run dev -- --port 3000
```

**Option 3: Check what's using the port**

```bash
# macOS/Linux
lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

Common processes that use port 5000:
- AirPlay Receiver (macOS Monterey+)
- Flask development server
- Other Node.js applications

### Disable AirPlay Receiver (macOS)

If AirPlay is using port 5000:

1. System Preferences → Sharing
2. Uncheck "AirPlay Receiver"

Or use a different port for your app.

## Environment Variables

The port configuration is independent of environment variables. The `VITE_API_BASE_URL` environment variable only controls the backend API URL, not the frontend port.

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000  # Backend URL (not frontend port)
```

## Docker Configuration

If running in Docker, expose port 5000:

```dockerfile
EXPOSE 5000
```

```bash
docker run -p 5000:5000 your-image
```

## Proxy Configuration

The frontend proxies `/api` requests to the backend:

```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

**Example:**
- Frontend URL: `http://localhost:5000/api/v1/products/scrape`
- Proxied to: `http://localhost:8000/api/v1/products/scrape`

## Production Deployment

Port 5000 is only for local development. In production:

- **Static Hosting** (Vercel, Netlify): No port configuration needed
- **Docker/VM**: Configure port in deployment config
- **Reverse Proxy** (Nginx): Configure upstream port

### Nginx Example

```nginx
server {
    listen 80;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Troubleshooting

### Problem: Dev server not starting

**Solution:**
```bash
# Check if port is available
lsof -i :5000

# Try different port
npm run dev -- --port 3000
```

### Problem: Can't access from other devices

**Solution:**
```bash
# Start with --host flag
npm run dev -- --host

# Check firewall settings
# Ensure port 5000 is allowed
```

### Problem: CORS errors

**Solution:**
1. Check backend is running on port 8000
2. Verify `VITE_API_BASE_URL` in `.env.development`
3. Check browser console for exact error
4. Ensure backend CORS allows `http://localhost:5000`

## Quick Reference

```bash
# Default start (port 5000)
npm run dev

# Custom port
npm run dev -- --port 3000

# Allow network access
npm run dev -- --host

# Custom port + network
npm run dev -- --port 3000 --host

# Check what's using a port
lsof -i :5000

# Kill process on port
lsof -ti:5000 | xargs kill -9
```

## Summary

- ✅ Default port: **5000**
- ✅ Backend API: **8000**
- ✅ Preview: **5000**
- ✅ Configured in: `vite.config.ts`
- ✅ Change temporarily: `npm run dev -- --port 3000`
- ✅ Network access: `npm run dev -- --host`
