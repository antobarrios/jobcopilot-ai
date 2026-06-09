# JobCopilot AI 🚀

API para automatizar postulaciones de trabajo. Este es el backend inicial construido con FastAPI.

### ✨ Features actuales
- **FastAPI** corriendo en `http://127.0.0.1:8000`
- **Endpoint `/`**: Health check
- **SQLite**: Base de datos lista para conectar
- **Estructura modular**: Carpeta `backend/` con `app/`, `main.py`, `requirements.txt`

### 🛠️ Stack
- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Base de datos**: SQLite
- **Control de versiones**: Git + GitHub

### 🚀 Cómo correrlo local
```bash
# 1. Clonar el repo
git clone https://github.com/antobarrios/jobcopilot-ai.git

# 2. Entrar a la carpeta
cd jobcopilot-ai

# 3. Instalar dependencias
pip install -r requirements.txt

26  
27  # 4. Correr el servidor
28  uvicorn main:app --reload
29  ```
30  API disponible en: `http://127.0.0.1:8000`
31  
32  ### 📍 Roadmap
33  - [ ] `POST /register`: Registro de usuarios
34  - [ ] `POST /login`: Login con JWT
35  - [ ] `GET /jobs`: Endpoint para obtener trabajos
36  - [ ] Deploy en Render
37  - [ ] Frontend en React
38  
39  ---
40  **Hecho con 💙 por Anto Barrios** | En construcción activa
