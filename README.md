# MatchCV

API REST que analiza CVs en PDF contra vacantes laborales usando IA.

Devuelve scoring de compatibilidad 0-100 + feedback accionable para mejorar tu postulación en menos de 5 segundos.

**Live Demo:** https://jobcopilot-ai-production.up.railway.app/docs

**Stack:** Python, FastAPI, Groq API, Llama 3.3 70B, Railway

## Endpoint

`POST /analizar-cv`

**Recibe:**
- `file`: CV en PDF
- `vacante`: Descripción de la vacante (texto)

**Devuelve:**
```json
{
  "score": 85,
  "fortalezas": ["Experiencia en Python", "Proyectos con FastAPI"],
  "a_mejorar": ["Agregar métricas de impacto", "Certificación cloud"],
  "consejo_clave": "Destacá tu experiencia con LLMs en el resumen"
}
