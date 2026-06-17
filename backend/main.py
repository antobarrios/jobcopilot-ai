# deploy 2026-06-17 MIGRADO A GROQ - JobCopilot funcionando
from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import json
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional
from dotenv import load_dotenv

# 1. CARGAR ENV PRIMERO
load_dotenv()

# 2. PATCH PROXIES ANTES DE IMPORTAR GROQ
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

from groq import Groq # Importar DESPUÉS del patch

# 3. TABLA TRABAJO
class Trabajo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    empresa: str
    ubicacion: str | None = None
    remoto: bool = True
    sueldo_usd: str | None = None
    url_original: str | None = None

# 4. CONEXION DB
sqlite_file_name = "jobcopilot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False) # echo=False para no llenar logs

# 5. CREAR DB
def crear_db_y_tablas():
    SQLModel.metadata.create_all(engine)

# 6. APP FASTAPI
app = FastAPI(title="JobCopilot API v2 - Groq")

# 7. CLIENTE GROQ
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 8. STARTUP
@app.on_event("startup")
def on_startup():
    crear_db_y_tablas()
    with Session(engine) as session:
        statement = select(Trabajo)
        results = session.exec(statement).first()
        if not results:
            trabajos_iniciales = [
                Trabajo(titulo="Backend Dev Jr", empresa="Tech SA", remoto=True, sueldo_usd="1000"),
                Trabajo(titulo="Python Developer", empresa="StarupXYZ", remoto=False, sueldo_usd="1000"),
                Trabajo(titulo="FastAPI Trainee", empresa="Software Factory", remoto=True, sueldo_usd="800")
            ]
            session.add_all(trabajos_iniciales)
            session.commit()

# 9. GET TRABAJOS
@app.get("/trabajos")
def listar_trabajos(remoto: Optional[bool] = None, sueldo_minimo: Optional[int] = None):
    with Session(engine) as session:
        statement = select(Trabajo)
        if remoto is not None:
            statement = statement.where(Trabajo.remoto == remoto)
        if sueldo_minimo is not None:
            statement = statement.where(Trabajo.sueldo_usd >= sueldo_minimo)
        trabajos = session.exec(statement).all()
        return {"cantidad": len(trabajos), "trabajos": trabajos}

# 10. POST TRABAJOS
@app.post("/trabajos", response_model=Trabajo)
def crear_trabajo(trabajo: Trabajo):
    with Session(engine) as session:
        session.add(trabajo)
        session.commit()
        session.refresh(trabajo)
        return trabajo

# 11. ANALIZAR CV CON GROQ
@app.post("/analizar-cv")
async def analizar_cv(file: UploadFile = File(...), vacante: str = ""):
    try:
        await file.read() # Leer para no dejar el stream abierto
        print(f"Analizando {file.filename} para: {vacante}")

        prompt = f"""Sos un recruiter senior. Analiza este CV para la vacante: {vacante}.
        El archivo se llama: {file.filename}

        No puedo leer el contenido del PDF. Da una respuesta genérica pero útil.
        Devolve SOLO un JSON válido con esta estructura exacta:
        {{
            "score": 75,
            "fortalezas": ["Experiencia relevante", "Stack técnico", "Soft skills"],
            "a_mejorar": ["Agregar métricas", "Optimizar keywords", "Formato ATS"],
            "consejo_clave": "Adapta el CV usando palabras clave de la vacante"
        }}"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192", # Modelo válido en 0.4.2
            temperature=0.3
        )

        result_text = chat_completion.choices[0].message.content
        print(f"Respuesta Groq: {result_text}")
        return json.loads(result_text)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Groq devolvió JSON inválido")
    except Exception as e:
        print(f"ERROR GROQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 12. MODELOS GROQ DISPONIBLES
@app.get("/modelos")
def listar_modelos():
    return [
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it"
    ]

# 13. ROOT
@app.get("/")
def root():
    return {"status": "JobCopilot funcionando con Groq", "docs": "/docs"}
