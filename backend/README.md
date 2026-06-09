# JobCopilot API v2
API REST para busqueda de trabajos tech construida con FastAPI + SQLModel.

![Swagger UI](./swagger-docs.png)

## Features 
Listado de trabajos con filtros dinamicos 
Query params: `remoto`, `sueldo_minimo`, `stack`
Documentacion Swagger automatica en `/docs`
Base de datos SQLite con seeding automatico 
Validacion con Pydantic 

## Uso 
```bash
uvicorn main:app --reload
```