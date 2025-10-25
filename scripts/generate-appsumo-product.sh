#!/bin/bash

# AppSumo Product Generator
# Usage: ./generate-appsumo-product.sh --name "ChatBot Pro" --slug "chatbot-pro" --port 3001

set -e

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name) PRODUCT_NAME="$2"; shift 2 ;;
        --slug) PRODUCT_SLUG="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        --tier1) TIER1_PRICE="$2"; shift 2 ;;
        --tier2) TIER2_PRICE="$2"; shift 2 ;;
        --tier3) TIER3_PRICE="$2"; shift 2 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

# Defaults
PRODUCT_NAME="${PRODUCT_NAME:-My Product}"
PRODUCT_SLUG="${PRODUCT_SLUG:-my-product}"
PORT="${PORT:-3000}"
TIER1_PRICE="${TIER1_PRICE:-59}"
TIER2_PRICE="${TIER2_PRICE:-119}"
TIER3_PRICE="${TIER3_PRICE:-199}"

PRODUCT_DIR="appsumo-products/${PRODUCT_SLUG}"

echo "🚀 Generating AppSumo Product: ${PRODUCT_NAME}"
echo "   Slug: ${PRODUCT_SLUG}"
echo "   Port: ${PORT}"

# Create directory structure
mkdir -p "${PRODUCT_DIR}"/{frontend,backend,docs}
mkdir -p "${PRODUCT_DIR}/frontend/src"/{pages,components,hooks,lib}
mkdir -p "${PRODUCT_DIR}/backend/app"/{api,services,models}

# ===== FRONTEND =====

cat > "${PRODUCT_DIR}/frontend/package.json" << EOF
{
  "name": "${PRODUCT_SLUG}",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.23.0",
    "axios": "^1.6.8",
    "@tanstack/react-query": "^5.32.0",
    "lucide-react": "^0.376.0",
    "framer-motion": "^11.1.7"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.2.10",
    "tailwindcss": "^3.4.3",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  }
}
EOF

cat > "${PRODUCT_DIR}/frontend/vite.config.js" << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: parseInt(process.env.PORT) || 3000 }
})
EOF

cat > "${PRODUCT_DIR}/frontend/tailwind.config.js" << 'EOF'
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: {} },
  plugins: []
}
EOF

cat > "${PRODUCT_DIR}/frontend/index.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${PRODUCT_NAME}</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
EOF

cat > "${PRODUCT_DIR}/frontend/src/main.jsx" << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
EOF

cat > "${PRODUCT_DIR}/frontend/src/index.css" << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

cat > "${PRODUCT_DIR}/frontend/src/App.jsx" << EOF
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import Dashboard from './pages/Dashboard'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
EOF

cat > "${PRODUCT_DIR}/frontend/src/pages/LandingPage.jsx" << EOF
import { motion } from 'framer-motion'
import { ArrowRight, Check } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 pt-20 pb-16">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            ${PRODUCT_NAME}
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Professional tool for blockchain analysis
          </p>
          <button className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 flex items-center gap-2 mx-auto">
            Get Started <ArrowRight size={20} />
          </button>
        </motion.div>
      </div>

      {/* Pricing */}
      <div className="max-w-7xl mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Pricing</h2>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { name: 'Tier 1', price: ${TIER1_PRICE}, features: ['Feature 1', 'Feature 2'] },
            { name: 'Tier 2', price: ${TIER2_PRICE}, features: ['All Tier 1', 'Feature 3', 'Feature 4'] },
            { name: 'Tier 3', price: ${TIER3_PRICE}, features: ['All Tier 2', 'Feature 5', 'Unlimited'] }
          ].map(tier => (
            <div key={tier.name} className="border rounded-lg p-6 bg-white shadow-sm">
              <h3 className="text-xl font-bold mb-2">{tier.name}</h3>
              <div className="text-4xl font-bold mb-4">\${tier.price}</div>
              <ul className="space-y-2">
                {tier.features.map(f => (
                  <li key={f} className="flex items-center gap-2">
                    <Check size={16} className="text-green-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
EOF

cat > "${PRODUCT_DIR}/frontend/src/pages/Dashboard.jsx" << EOF
export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">${PRODUCT_NAME} Dashboard</h1>
      <div className="bg-white rounded-lg shadow p-6">
        <p>Dashboard content goes here</p>
      </div>
    </div>
  )
}
EOF

# ===== BACKEND =====

cat > "${PRODUCT_DIR}/backend/requirements.txt" << 'EOF'
fastapi==0.110.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
python-dotenv==1.0.1
sqlalchemy==2.0.29
psycopg2-binary==2.9.9
redis==5.0.3
EOF

cat > "${PRODUCT_DIR}/backend/app/main.py" << EOF
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="${PRODUCT_NAME} API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "${PRODUCT_NAME} API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# ===== DOCKER =====

cat > "${PRODUCT_DIR}/docker-compose.yml" << EOF
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/${PRODUCT_SLUG}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "${PORT}:3000"
    environment:
      - VITE_API_URL=http://localhost:8000

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=${PRODUCT_SLUG}
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
EOF

cat > "${PRODUCT_DIR}/backend/Dockerfile" << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "app.main"]
EOF

cat > "${PRODUCT_DIR}/frontend/Dockerfile" << 'EOF'
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
EOF

# ===== README =====

cat > "${PRODUCT_DIR}/README.md" << EOF
# ${PRODUCT_NAME}

AppSumo Lifetime Deal Product

## Quick Start

\`\`\`bash
cd appsumo-products/${PRODUCT_SLUG}
docker-compose up
\`\`\`

Frontend: http://localhost:${PORT}
Backend API: http://localhost:8000

## Pricing

- Tier 1: \$${TIER1_PRICE}
- Tier 2: \$${TIER2_PRICE}
- Tier 3: \$${TIER3_PRICE}

## Status

✅ MVP Ready for AppSumo Launch
EOF

echo "✅ Product generated successfully!"
echo "📁 Location: ${PRODUCT_DIR}"
echo "🚀 Next: cd ${PRODUCT_DIR} && docker-compose up"
