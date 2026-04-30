import subprocess
import httpx
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("claro-wfm")

BASE_URL = "http://localhost:5000"

@mcp.tool()
def ver_logs(lineas: int = 50) -> str:
    """Muestra las últimas líneas del log de la app"""
    log_path = Path("/var/www/claro_wfm/claro_app/logs")
    logs = list(log_path.glob("*.log"))
    if not logs:
        return "No se encontraron archivos de log"
    ultimo = max(logs, key=lambda f: f.stat().st_mtime)
    result = subprocess.run(["tail", f"-{lineas}", str(ultimo)], capture_output=True, text=True)
    return result.stdout

@mcp.tool()
def leer_archivo(ruta: str) -> str:
    """Lee un archivo del proyecto"""
    return Path(ruta).read_text(encoding="utf-8")

@mcp.tool()
def escribir_archivo(ruta: str, contenido: str) -> str:
    """Escribe o edita un archivo del proyecto"""
    Path(ruta).write_text(contenido, encoding="utf-8")
    return f"Guardado: {ruta}"

@mcp.tool()
def listar_archivos(directorio: str = "/var/www/claro_wfm/claro_app") -> str:
    """Lista archivos del proyecto"""
    result = subprocess.run(
        ["find", directorio, "-type", "f", "-not", "-path", "*/venv/*"],
        capture_output=True, text=True
    )
    return result.stdout

@mcp.tool()
def docker_logs(lineas: int = 50) -> str:
    """Muestra logs del contenedor Docker"""
    result = subprocess.run(
        ["docker", "compose", "logs", f"--tail={lineas}"],
        capture_output=True, text=True,
        cwd="/var/www/claro_wfm/claro_app"
    )
    return result.stdout or result.stderr

@mcp.tool()
def docker_estado() -> str:
    """Muestra el estado de los contenedores"""
    result = subprocess.run(
        ["docker", "compose", "ps"],
        capture_output=True, text=True,
        cwd="/var/www/claro_wfm/claro_app"
    )
    return result.stdout

@mcp.tool()
def llamar_api(endpoint: str, metodo: str = "GET", payload: dict = None) -> dict:
    """Llama a un endpoint de tu app"""
    with httpx.Client(timeout=10) as client:
        response = client.request(metodo, f"{BASE_URL}{endpoint}", json=payload)
        return {"status": response.status_code, "body": response.text[:2000]}

if __name__ == "__main__":
    mcp.run(transport="stdio")
