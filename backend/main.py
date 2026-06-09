from fastapi import FastAPI
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional 

# 1. DEFINIMOS LA TABLA "TRABAJO"
class Trabajo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    empresa: str  
    remoto: bool
    sueldo_usd: int 

# 2. CONECTAMOS A LA BASE DE DATOS 
sqlite_file_name = "jobcopilot.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url,echo=True)

# 3. CREAMOS LA BASE SI NO EXISTE 
def crear_db_y_tablas():
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
            sueldo_usd=1000)
            trabajo2 = Trabajo(titulo="Python Developer",
            empresa="StarupXYZ", remoto=False,
            sueldo_usd=1000)
            trabajo3 = Trabajo(titulo="FastAPI Trainee",
            empresa="Software Factory",
            remoto=True, sueldo_usd=800)
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
    @app.post("/trabajos")
    def crear_trabajo(trabajo: Trabajo):
        with Session(engine) as session:
            session.add(trabajo)
            session.commit()
            session.refresh(trabajo)
            return trabajo 