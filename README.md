# WatchLens 🔍⌚

Plataforma de descoberta de relógios por busca visual (IA), texto e filtros avançados.

## Funcionalidades

- 📸 **Busca por imagem** — envie uma foto e encontre o relógio exato ou os mais similares (score 0–100%)
- 🔍 **Busca por texto** — por marca, modelo ou referência, com autocomplete
- 🎛️ **Filtros avançados** — estilo, era, cor do mostrador, material, bezel, movimento, diâmetro, período
- 📊 **Score de similaridade** — 70% embedding visual (CLIP) + 30% atributos técnicos
- 🎯 **Catálogo curado** — 29+ referências icônicas: Rolex, Patek Philippe, Audemars Piguet, Omega, IWC, Tudor, Seiko, Cartier...

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, TanStack React Query |
| Backend | FastAPI, SQLAlchemy, Python 3.11+ |
| Banco (dev) | SQLite |
| Banco (prod) | PostgreSQL (Railway) |
| Embeddings | CLIP ViT-B-32 via sentence-transformers |
| Deploy | Vercel (frontend) + Railway (backend) |

## Rodar localmente

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_catalog.py
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:3000 (frontend) | http://localhost:8000/docs (API)

## Testes
```bash
cd backend
pytest tests/ -v
# 22/22 testes passando ✅
```

## Deploy

### Railway (backend)
1. Crie um projeto no [Railway](https://railway.app)
2. Conecte este repositório
3. Defina root directory: `backend`
4. Adicione variáveis de ambiente:
   - `DATABASE_URL` = URL do PostgreSQL do Railway
   - `CORS_ORIGINS` = URL do frontend no Vercel
   - `ENVIRONMENT` = production

### Vercel (frontend)
1. Importe o repositório no [Vercel](https://vercel.com)
2. Defina root directory: `frontend`
3. Adicione variável de ambiente:
   - `NEXT_PUBLIC_API_URL` = URL do backend no Railway
