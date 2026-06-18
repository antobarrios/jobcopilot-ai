import requests
import time
print("1. Script iniciado")
API_URL = "https://jobcopilot-ai-production.up.railway.app/trabajos"
print("2. URL de API lista")
def scrapear_remotive():
    print("3. Entrando a la funcion")
    
    url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=30"
    print(f"URL real: {repr(url)}")
    
    print("4. Haciendo GET a Remotive...")
    try:
       res = requests.get(url, timeout=15, verify=False)
       print(f"5. Status de Remotive: {res.status_code}")
    except Exception as e:
        print(f"Error: {type(e).__name__}")
        print(f"DETALLE: {e}")
    if res.status_code!= 200:
        return
    
    jobs = res.json()["jobs"]
    print(f"6. Remotive devolvio {len(jobs)} trabajos")
    agregados = 0
    
    for job in jobs:
        nuevo_trabajo = {
            "titulo": job["title"],
            "empresa": job["company_name"],
            "remoto": True,
            "sueldo_usd": job.get("salary") or "A consultar",
            "url_original": job["url"]
            
        }
        print(f"7. Mandando POST: {job['title']}")
        r= requests.post(API_URL, json=nuevo_trabajo)
        if r.status_code == 200:
            agregados += 1
            print(f"  OK: {job['title']}")
        else:
            print(f" Fallo: {r.status_code} - {r.text}")
        time.sleep(1)
        print(f"8.Terminando. Se agregaron {agregados} trabajos nuevos")
if __name__ == "__main__":
    print("9. Llamando a la funcion main")
    scrapear_remotive()    
