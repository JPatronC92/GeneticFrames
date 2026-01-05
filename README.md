# 🧬 GeneticFrames - Digital Art Zoo

**GeneticFrames** es una plataforma que transforma datos genéticos en arte digital interactivo. Utiliza secuencias de ADN para generar "Firmas Genómicas" visuales únicas, permitiendo explorar la belleza oculta en el código de la vida.

Este proyecto opera como un "Zoológico de Arte Digital", donde los usuarios pueden buscar especies, visualizar sus estructuras moleculares y ver cómo mutaciones genéticas afectarían su representación artística.

---

## 🏗️ Arquitectura

GeneticFrames utiliza una arquitectura híbrida de microservicios:

*   **Frontend**: React + Vite + TypeScript (en `geneticframes-web/`)
    *   Visualizaciones 3D con Three.js y React-Three-Fiber.
    *   Estilizado con TailwindCSS.
    *   Gestión de estado con React Query.
*   **Backend**: FastAPI (Python) (en `geneticframes-api/`)
    *   Análisis de ADN con BioPython.
    *   Integración con NCBI Entrez API y AlphaFold DB.
    *   Caché con Redis.
    *   Despliegue configurado para Render.

### Diagrama Simplificado

```mermaid
graph TD
    Client[Frontend (React)] -->|REST| API[Backend (FastAPI)]
    API -->|Análisis| BioPython
    API -->|Datos| NCBI[NCBI Entrez]
    API -->|Estructura| AlphaFold
    API -->|Caché| Redis
```

---

## ✨ Características Principales

1.  **Firma Genómica**: Algoritmo que transforma secuencias de ADN en parámetros visuales (colores, formas) de manera determinística.
2.  **Simulador de Mutaciones**: Permite visualizar cómo cambios en el ADN afectan la obra de arte generada.
3.  **Exhibiciones**: Agrupación temática de especies (e.g., "Deep Sea Giants").
4.  **Búsqueda de Especies**: Conexión directa con bases de datos científicas.

---

## 🚀 Configuración Local

### Prerrequisitos
*   Python 3.11+
*   Node.js 18+
*   Redis (opcional para desarrollo local, recomendado)

### 1. Backend (`geneticframes-api`)

```bash
cd geneticframes-api
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
El servidor API estará corriendo en `http://localhost:8000`.

### 2. Frontend (`geneticframes-web`)

```bash
cd geneticframes-web
npm install
npm run dev
```
La aplicación web estará disponible en `http://localhost:5173`.

> **Nota**: Asegúrate de que el frontend apunte al backend correcto configurando `VITE_API_URL` en un archivo `.env` si es necesario (por defecto intenta conectar a localhost:8000).

---

## ☁️ Guía de Despliegue (Render)

Este repositorio incluye un archivo `render.yaml` ("Blueprint") para automatizar el despliegue del backend en **Render**.

1.  Crea una cuenta en [Render.com](https://render.com).
2.  Ve a **Blueprints** > **New Blueprint Instance**.
3.  Conecta este repositorio de GitHub/GitLab.
4.  Render detectará automáticamente la configuración y creará:
    *   Un servicio Web para la API (`geneticframes-api`).
    *   Una instancia de Redis (`geneticframes-redis`).
5.  Una vez desplegado, copia la URL de tu servicio API (ej. `https://geneticframes-api.onrender.com`).

### Configuración del Frontend (Vercel/Netlify)

Para el frontend, se recomienda usar Vercel o Netlify:
1.  Importa el subdirectorio `geneticframes-web`.
2.  Configura la variable de entorno `VITE_API_URL` con la URL de tu backend desplegado en Render.
3.  Despliega.

---

## 🗺️ Roadmap y Estado

Para más detalles sobre el estado actual, riesgos técnicos y planes futuros, consulta:
*   [ARCHITECTURE_AND_ROADMAP.md](./ARCHITECTURE_AND_ROADMAP.md) - Documentación técnica detallada.
*   [MVP_PROPOSAL.md](./MVP_PROPOSAL.md) - Propuesta y alcance del MVP.
