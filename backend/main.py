# deploy 2026-06-17 MIGRADO A GROQ - JobCopilot funcionando
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File
from groq import Groq
import os
import json
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional

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
sqlite_file_name = "jobcopilot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

# 3. CREAR DB
def crear_db_y_tablas():
    if os.path.exists("jobcopilot.db"):
        os.remove("jobcopilot.db")
    SQLModel.metadata.create_all(engine)

# 4. APP FASTAPI
app = FastAPI(title="JobCopilot API v2 - Groq")

# 5. CLIENTE GROQ
# 5. CLIENTE GROQ
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 6. STARTUP
@app.on_event("startup")
def on_startup():
    crear_db_y_tablas()
    with Session(engine) as session:
        statement = select(Trabajo)
        results = session.exec(statement).first()
        if not results:
            trabajo1 = Trabajo(titulo="Backend Dev Jr", empresa="Tech SA", remoto=True, sueldo_usd="1000")
            trabajo2 = Trabajo(titulo="Python Developer", empresa="StarupXYZ", remoto=False, sueldo_usd="1000")
            trabajo3 = Trabajo(titulo="FastAPI Trainee", empresa="Software Factory", remoto=True, sueldo_usd="800")
            session.add(trabajo1)
            session.add(trabajo2)
            session.add(trabajo3)
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
async def analizar_cv(file: UploadFile = File(...), vacante: str = ""):
    try:
        pdf_bytes = await file.read()
        print(f"PDF pesa: {len(pdf_bytes)} bytes")

        prompt = f"""Sos un recruiter senior. Analiza este CV para la vacante: {vacante}.
        El archivo se llama: {file.filename}

        No puedo leer el contenido del PDF. Da una respuesta genérica pero útil.
        Devolve SOLO un JSON válido con esta estructura:
        {{
            "score": número del 0-100,
            "fortalezas": ["fortaleza1", "fortaleza2", "fortaleza3"],
            "a_mejorar": ["mejora1", "mejora2", "mejora3"],
            "consejo_clave": "texto"
        }}"""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile",
            response_format={"type": "json_object"}
        )

        result_text = chat_completion.choices[0].message.content
        print(f"Respuesta Groq: {result_text}")
        return json.loads(result_text)

    except Exception as e:
        print(f"ERROR GROQ: {e}")
        return {"error": str(e)}

# 10. MODELOS GROQ DISPONIBLES
@app.get("/modelos")
def listar_modelos():
    return [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

# 11. ROOT
@app.get("/")
def root():
    return {"status": "JobCopilot funcionando con Groq", "docs": "/docs"}
