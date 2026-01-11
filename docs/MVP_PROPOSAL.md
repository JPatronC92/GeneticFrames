# 🧬 GeneticFrames - Documentación Técnica y Arquitectura

## 🎯 Arquitectura del Sistema

### **Opción A: Stack Moderno Full-Stack**

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  Next.js 14 + TypeScript + Tailwind CSS + Framer Motion     │
│  - Server Components para SSR                                │
│  - Client Components para interactividad                     │
│  - Three.js/React-Three-Fiber para visualizaciones 3D        │
└─────────────────────────────────────────────────────────────┘
                              ↓ REST/GraphQL
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND API                             │
│  FastAPI (Python) + Redis + Celery                          │
│  - Endpoints REST optimizados                                │
│  - WebSockets para generación en tiempo real                │
│  - Worker tasks para procesamiento pesado                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   DATA & PROCESSING                          │
│  • BioPython (análisis genético)                            │
│  • NumPy/SciPy (procesamiento matemático)                   │
│  • Plotly/D3.js (generación de gráficos)                    │
│  • Supabase/PostgreSQL (base de datos)                      │
│  • Redis (caché de secuencias)                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL APIS                              │
│  • NCBI Entrez (secuencias ADN)                             │
│  • GBIF (taxonomía)                                          │
│  • Cloudflare R2/S3 (almacenamiento imágenes)               │
└─────────────────────────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Mejor UX/UI con Next.js
- ✅ Visualizaciones 3D interactivas (Three.js)
- ✅ Escalabilidad horizontal con FastAPI + Celery
- ✅ SEO optimizado (SSR)
- ✅ Carga ultra-rápida con edge computing

**Desventajas:**
- ⚠️ Requiere aprender JavaScript/TypeScript
- ⚠️ Mayor complejidad inicial

---

### **Opción B: Stack Python Optimizado**

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND MEJORADO                         │
│  Streamlit + Custom Components (React)                      │
│  - streamlit-extras para componentes avanzados              │
│  - streamlit-plotly-events para interactividad              │
│  - Custom CSS/JS injection                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND OPTIMIZADO                          │
│  • FastAPI microservice (generación async)                  │
│  • Streamlit (interfaz principal)                           │
│  • Supabase (backend-as-a-service)                          │
│  • Redis/Upstash (caché distribuido)                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    PROCESAMIENTO                             │
│  • BioPython (core sin cambios)                             │
│  • Plotly/Matplotlib (visualización)                        │
│  • Pillow (exportación imágenes)                            │
└─────────────────────────────────────────────────────────────┘
```

**Ventajas:**
- ✅ Mantiene código Python existente
- ✅ Menor curva de aprendizaje
- ✅ Prototipado ultra-rápido

**Desventajas:**
- ⚠️ Limitaciones de Streamlit para UX avanzada
- ⚠️ Menor flexibilidad de diseño
- ⚠️ Performance limitada para alto tráfico

---

### **Opción C: Hybrid Stack** ⭐ **RECOMENDADO**

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React/Vue + Vite + TailwindCSS                             │
│  - Interfaz moderna y rápida                                │
│  - Componentes de @shadcn/ui                                │
│  - React Query para estado del servidor                     │
└─────────────────────────────────────────────────────────────┘
                              ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API                               │
│  FastAPI (Python 3.11)                                      │
│  ├── /api/search (búsqueda de especies)                     │
│  ├── /api/generate (generación de arte)                     │
│  ├── /api/export (descarga imágenes)                        │
│  └── /api/gallery (galería pública)                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  SERVICIOS & DATA                            │
│  • Supabase (PostgreSQL + Auth + Storage)                   │
│  • Upstash Redis (caché de secuencias NCBI)                 │
│  • Cloudflare Workers (edge compute opcional)               │
│  • BioPython + NumPy (procesamiento)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologías

### **Frontend (UI/UX)**

| Tecnología | Uso | Por qué |
|------------|-----|---------|
| **Vite + React 18** | Framework base | Renderizado ultra-rápido, HMR instantáneo |
| **TailwindCSS + shadcn/ui** | Diseño | Componentes modernos pre-construidos |
| **Three.js + React-Three-Fiber** | Visualización 3D | Arte genético en 3D (diferenciador único) |
| **Framer Motion** | Animaciones | Transiciones fluidas y profesionales |
| **React Query (TanStack)** | Estado servidor | Caché automático, revalidación inteligente |
| **Zustand** | Estado cliente | Gestión de estado simple y potente |
| **Recharts/Visx** | Gráficos 2D | Alternativa ligera a Plotly |

### **Backend (API & Procesamiento)**

| Tecnología | Uso | Por qué |
|------------|-----|---------|
| **FastAPI** | API REST | Async nativo, validación automática, docs |
| **Pydantic V2** | Validación | Tipos seguros, serialización rápida |
| **Celery + Redis** | Tareas async | Generación de arte sin bloquear |
| **BioPython** | ADN analysis | Mantener (ya funciona bien) |
| **Pillow + CairoSVG** | Exportación | PNG/SVG/PDF de alta calidad |
| **LangChain (opcional)** | IA generativa | Descripciones de especies con GPT-4 |

### **Base de Datos & Storage**

| Tecnología | Uso | Por qué |
|------------|-----|---------|
| **Supabase** | PostgreSQL + Auth + Storage | Todo-en-uno, tier gratuito generoso |
| **Upstash Redis** | Caché distribuido | Edge locations, pay-per-request |
| **Cloudflare R2** | Almacenamiento imágenes | Más barato que S3, sin egress fees |
| **Turso (SQLite)** | Alternativa ligera | Edge database, ultra-rápido |

### **Deployment & DevOps**

| Tecnología | Uso | Por qué |
|------------|-----|---------|
| **Vercel** | Frontend hosting | Deploy automático, edge functions |
| **Railway/Fly.io** | Backend API | Escalado automático, fácil setup |
| **GitHub Actions** | CI/CD | Tests automáticos, deploy |
| **Sentry** | Error tracking | Monitoreo en producción |
| **PostHog** | Analytics | Understand user behavior |

### **Alternativas Fuera de Python**

#### **Visualización Avanzada**

1. **Three.js + GLSL Shaders**: Arte genético en 3D con efectos visuales impresionantes
   ```javascript
   // Ejemplo: ADN en 3D rotando
   const dnaHelix = new DNA3DHelix({
       sequence: "ATCG...",
       gcContent: 0.42,
       rotation: true,
       particles: true
   });
   ```

2. **P5.js**: Generative art basado en Processing
   - Perfecto para arte procedural
   - Fácil de integrar con React
   - Exportación a GIF/MP4

3. **Rive**: Animaciones vectoriales interactivas
   - Más ligero que Lottie
   - Mejor performance
   - Editor visual

#### **Backend Alternativo**

1. **Bun + Hono**: JavaScript/TypeScript ultra-rápido
   ```typescript
   // API endpoint en Bun (3x más rápido que Node)
   app.post('/api/generate', async (c) => {
       const { species } = await c.req.json();
       const dna = await fetchDNA(species);
       return c.json({ art: generateArt(dna) });
   });
   ```

2. **Go + Fiber**: Performance extrema
   - Binarios compilados
   - Bajo uso de memoria
   - Ideal para procesamiento pesado

3. **Rust + Actix-Web**: Máximo performance
   - Zero-cost abstractions
   - Memory safety
   - Para procesar millones de bases

---

## 🎨 Funcionalidades Clave

### **1. Visualización 3D Interactiva**
- Doble hélice de ADN en 3D rotando
- Zoom a nivel de bases nitrogenadas
- Exportar como modelo 3D (GLB/OBJ)

### **2. Modo "Time-Lapse Evolution"**
- Visualizar cómo cambiaría el arte si el ADN mutara
- Comparar especies relacionadas
- Animación de divergencia evolutiva

### **3. Educational Mode**
- Explicaciones interactivas de cada parámetro genético
- Quiz sobre genética
- Colaboración con escuelas/universidades

### **4. API Pública**
- Freemium model
- Documentación con ejemplos
- SDKs en Python/JavaScript/Go

---

## 🚀 Quick Start

### **Opción A (Next.js Full-Stack)**
```bash
npx create-next-app@latest geneticframes --typescript --tailwind --app
cd geneticframes
npm install @tanstack/react-query three @react-three/fiber
npm install @supabase/supabase-js zustand framer-motion
```

### **Opción B (Streamlit Optimizado)**
```bash
cd GeneticFrames
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install streamlit==1.38.0 fastapi uvicorn redis
pip install streamlit-extras streamlit-plotly-events
```

### **Opción C (Hybrid - Recomendado)** ⭐
```bash
# Frontend
npm create vite@latest geneticframes-web -- --template react-ts
cd geneticframes-web
npm install && npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Backend
cd ..
mkdir geneticframes-api && cd geneticframes-api
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn redis celery biopython supabase
```

---

## 📚 Recursos de Aprendizaje

### **Frontend React + Three.js**
- 🎓 [React Three Fiber Journey](https://threejs-journey.com/)
- 🎓 [shadcn/ui Docs](https://ui.shadcn.com/)
- 🎓 [TailwindCSS Tutorial](https://tailwindcss.com/docs)

### **Backend FastAPI**
- 🎓 [FastAPI Official Tutorial](https://fastapi.tiangolo.com/tutorial/)
- 🎓 [Real Python - FastAPI](https://realpython.com/fastapi-python-web-apis/)
- 🎓 [TestDriven.io - FastAPI Best Practices](https://testdriven.io/blog/fastapi-best-practices/)

### **DevOps & Deploy**
- 🎓 [Vercel Docs](https://vercel.com/docs)
- 🎓 [Railway Docs](https://docs.railway.app/)
- 🎓 [Supabase University](https://supabase.com/docs)
