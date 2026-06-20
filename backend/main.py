# deploy 2026-06-17 MIGRADO A GROQ - JobCopilot funcionando
import os

# === PATCH PROXIES ANTES DE CUALQUIER IMPORT DE GROQ ===
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
import json
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional
from groq import Groq # AHORA SÍ, después del patch

# 1. TABLA TRABAJO
class Trabajo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    empresa: str
    ubicacion: str | None = None
    remoto: bool = True
    sueldo_usd: str | None = None
    url_original: str | None = None

# 2. CONEXION DB
sqlite_file_name = "matchcv.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

# 3. CREAR DB
def crear_db_y_tablas():
    SQLModel.metadata.create_all(engine)

# 4. APP FASTAPI
app = FastAPI(title="MatchCV API v2 - Groq")
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MatchCV API v2 - Groq")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://matchcv-navy.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 5. CLIENTE GROQ
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 6. STARTUP
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

# 7. GET TRABAJOS
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

# 8. POST TRABAJOS
@app.post("/trabajos", response_model=Trabajo)
def crear_trabajo(trabajo: Trabajo):
    with Session(engine) as session:
        session.add(trabajo)
        session.commit()
        session.refresh(trabajo)
        return trabajo

# 9. ANALIZAR CV CON GROQ
@app.post("/analizar-cv")
@app.post("/analyze")
async def analizar_cv(file: UploadFile = File(...), vacante: str = ""):
    try:
        await file.read()
        prompt = f"""Sos un recruiter senior. Analiza este CV para la vacante: {vacante}.
        El archivo se llama: {file.filename}
        Devolve SOLO un JSON válido: {{"score": 75, "fortalezas": ["..."], "a_mejorar": ["..."], "consejo_clave": "..."}}"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        result_text = chat_completion.choices[0].message.content
        return json.loads(result_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Groq: {str(e)}")

# 10. MODELOS GROQ DISPONIBLES
@app.get("/modelos")
def listar_modelos():
    return ["mixtral-8x7b-32768", "llama2-70b-4096", "gemma-7b-it"]

# 11. ROOT
@app.get("/")
def root():
    return {"status": "MatchCV funcionando con Groq", "docs": "/docs"}
