from dotenv import load_dotenv 
load_dotenv()
from wfastapi import FastAPI, UploadFile
from google import genai
import os 
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional 

# 1. DEFINIMOS LA TABLA "TRABAJO"
class Trabajo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    empresa: str
    ubicacion: str | None = None
    remoto: bool = True
    sueldo_usd: str | None = None
    url_original: str | None = None
   

# 2. CONECTAMOS A LA BASE DE DATOS 
sqlite_file_name = "jobcopilot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url,echo=True)

# 3. CREAMOS LA BASE SI NO EXISTE 
def crear_db_y_tablas():
    import os
    if os.path.exists("jobcopilot.db"):
        os.remove("jobcopilot.db")
    SQLModel.metadata.create_all(engine)

# 4. CREAMOS LA APP 
app = FastAPI(title="JobCopilot API v2")

# 5. ESTO SE EJECUTA CUANDO ARRANCA LA APP 
@app.on_event("startup")
def on_startup():
    crear_db_y_tablas()
    # AGREGAMOS DATOS DE PRUEBA SI LA BASE ESTA VACIA
    with Session(engine) as session:
        statement = select(Trabajo)
        results = session.exec(statement).first()
        if not results: #Si no hay nada, cargamos los 3 trabajos
            trabajo1 = Trabajo(titulo="Backend Dev Jr", 
            empresa="Tech SA", remoto=True,
            sueldo_usd="1000")
            trabajo2 = Trabajo(titulo="Python Developer",
            empresa="StarupXYZ", remoto=False,
            sueldo_usd="1000")
            trabajo3 = Trabajo(titulo="FastAPI Trainee",
            empresa="Software Factory",
            remoto=True, sueldo_usd="800")
            session.add(trabajo1)
            session.add(trabajo2)
            session.add(trabajo3)
            session.commit()
# 6. ENDPOINT GET CON BASE DE DATOS 
@app.get("/trabajos") 
def listar_trabajos(remoto:Optional[bool]=None,sueldo_minimo:Optional[int]=None):
    with Session(engine) as session:
        statement = select(Trabajo)
        if remoto is not None: 
            statement = statement.where(Trabajo.remoto == remoto) 
        if sueldo_minimo is not None: 
            statement = statement.where(Trabajo.sueldo_usd >= sueldo_minimo)
        trabajos = session.exec(statement).all()
        return {"cantidad": len(trabajos), "trabajos": trabajos}    
    # 7. ENDPOINT POST PARA AGREGAR TRABAJOS NUEVOS
@app.post("/trabajos", response_model=Trabajo)
def crear_trabajo(trabajo: Trabajo):
    with Session(engine) as session:
        session.add(trabajo)
        session.commit()
        session.refresh(trabajo)
        return trabajo
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
@app.post("/analizar-cv")
async def analizar_cv(file:UploadFile,vacante:str):
    try:
        pdf_bytes = await file.read()
        print(f"PDF pesa: {len(pdf_bytes)} bytes")
        
        prompt = f"""Sos un recruiter senior. Analiza este CV para la vacante: {vacante}.
        Devolve SOLO un JSON con: score del 0-100, 3 fortalezas, 3 cosas a mejorar."""
        
        result = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
        print(f"Respuesta Gemini:{result.text}")
        return {"resultado":result.text}
    except Exception as e:
        print(f"ERROR REAL DE GEMINI:{e}")
        return {"error": str(e)}
