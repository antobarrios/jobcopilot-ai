# deploy 2026-06-20 MATCHCV FINAL - GROQ + PDF READER
import os
import json
import io

# === PATCH PROXIES ANTES DE CUALQUIER IMPORT DE GROQ ===
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(var, None)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional
from groq import Groq
import PyPDF2

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

# 9. ANALIZAR CV CON GROQ - VERSIÓN RECRUITER SALVAJE
@app.post("/analizar-cv")
@app.post("/analyze")
async def analizar_cv(file: UploadFile = File(...), descripcion: str = Form("")):
    try:
        contenido_cv = await file.read()

        # Extraer texto del PDF o TXT
        cv_text = ""
        if file.filename.lower().endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contenido_cv))
            for page in pdf_reader.pages:
                cv_text += page.extract_text() or ""
        else:
            cv_text = contenido_cv.decode('utf-8', errors='ignore')

        if not cv_text.strip():
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del CV. Si es PDF escaneado no funciona.")

        prompt = f"""Analizá este CV contra esta oferta laboral. Adaptá el análisis al rubro de la oferta: si es IT hablá de stacks, si es TCP de licencia ANAC, si es salud de matrículas.

OFERTA LABORAL:
{descripcion}

CV DEL CANDIDATO:
{cv_text}

DEBERÁS DEVOLVER ÚNICAMENTE UN JSON VÁLIDO CON EXACTAMENTE ESTAS KEYS:
{{
  "match_percentage": 78,
  "verdict": "Resumen brutal de 1 línea: ¿por qué sí o por qué no?",
  "strengths": ["Dato específico del CV que sirve para ESTA oferta", "Otro dato fuerte", "Otro más"],
  "gaps": ["Requisito clave de la oferta que NO aparece en el CV", "Otro gap crítico"],
  "ats_score": "72% - Explicación corta de por qué los bots te filtran o no",
  "recommendations": ["Hack CV: 1 cambio específico para subir el match +15% YA", "Qué decir en entrevista sobre el gap más grande", "Veredicto final: ¿Lo llaman o lo descartan y por qué?"]
}}

REGLAS: 1. Solo datos reales del CV 2. Sin frases genéricas tipo 'buena experiencia' 3. Si el CV no tiene nada que ver, poné match_percentage bajo y explicalo."""

        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        result_text = chat_completion.choices[0].message.content
        return json.loads(result_text)

    except Exception as e:
        print(f"ERROR DETALLE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al analizar CV: {str(e)}")

# 10. MODELOS GROQ DISPONIBLES
@app.get("/modelos")
def listar_modelos():
    return ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]

# 11. ROOT
@app.get("/")
def root():
    return {"status": "MatchCV funcionando con Groq", "docs": "/docs"}
