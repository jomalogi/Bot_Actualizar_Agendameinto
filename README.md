# 🚀 Agendamiento WFM — Claro

Sistema web para automatizar el agendamiento masivo de órdenes de trabajo
en el Módulo de Gestión de Claro. Múltiples usuarios, progreso en tiempo real.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│  Navegador del usuario                              │
│  ┌─────────────┐   WebSocket   ┌─────────────────┐  │
│  │  dashboard  │◄─────────────►│   Flask + SIO   │  │
│  │  + progreso │   HTTP/REST   │   (puerto 5000) │  │
│  └─────────────┘               └────────┬────────┘  │
└──────────────────────────────────────── │ ──────────┘
                                          │ Celery task
                              ┌───────────▼──────────┐
                              │   Celery Worker(s)   │
                              │   Selenium Headless  │
                              │   Chrome → Claro     │
                              └───────────┬──────────┘
                                          │
                    ┌─────────────────────┼──────────────┐
                    │                     │              │
             ┌──────▼──────┐      ┌───────▼─────┐  ┌────▼────┐
             │   MySQL     │      │    Redis    │  │ Excel   │
             │  (usuarios, │      │  (broker +  │  │ outputs │
             │  trabajos,  │      │  progreso)  │  │         │
             │  resultados)│      └─────────────┘  └─────────┘
             └─────────────┘
```

---

## 📋 Requisitos del servidor

- Ubuntu 20.04 / 22.04
- Python 3.10+
- MySQL 5.7+
- Redis 6+
- Google Chrome (se instala automáticamente)
- 2 GB RAM mínimo

---

## ⚡ Instalación rápida

### 1. Copiar archivos al servidor

```bash
scp -r claro_app/ usuario@tu-servidor:/opt/claro_app
ssh usuario@tu-servidor
cd /opt/claro_app
```

### 2. Configurar credenciales

Edita `config.py`:
```python
MYSQL_HOST     = "localhost"
MYSQL_USER     = "tu_usuario_mysql"
MYSQL_PASSWORD = "tu_password_mysql"
MYSQL_DB       = "claro_agendamiento"
```

O usa variables de entorno (recomendado):
```bash
export MYSQL_PASSWORD="tu_password"
export SECRET_KEY="clave_secreta_larga_y_random"
```

### 3. Crear base de datos MySQL

```sql
CREATE DATABASE claro_agendamiento CHARACTER SET utf8mb4;
CREATE USER 'claro_app'@'localhost' IDENTIFIED BY 'password_seguro';
GRANT ALL PRIVILEGES ON claro_agendamiento.* TO 'claro_app'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Instalar y arrancar

```bash
chmod +x install.sh start.sh
bash install.sh
source venv/bin/activate
flask init-db           # Crea tablas + usuario admin
bash start.sh           # Arranca todo
```

### 5. Acceder

```
http://IP-DEL-SERVIDOR:5000
Usuario: admin
Contraseña: Admin123!
```

---

## 👤 Flujo de uso

1. **Admin** crea cuentas para cada persona en `/admin/usuarios`
2. Cada usuario entra a `/perfil` y configura **su usuario y contraseña del módulo Claro**
3. Usuario sube su Excel desde el dashboard
4. El sistema procesa las órdenes en segundo plano con Selenium headless
5. El progreso se ve en tiempo real en la pantalla
6. Al terminar, se descarga el Excel con resultados y colores por estado

---

## 📊 Estructura del Excel de entrada

| numero_orden | tipo_orden       |
|-------------|------------------|
| 465762403   | Orden de Trabajo |
| 465779143   | Orden de Trabajo |

> Las columnas `Estado`, `Detalle`, `Procesado_en` se agregan automáticamente al resultado.

---

## 🎨 Estados en el Excel resultado

| Estado               | Color    | Significado                        |
|---------------------|----------|------------------------------------|
| AGENDADO            | 🟢 Verde  | Nueva agenda exitosa               |
| RE-AGENDADO         | 🔵 Azul   | Re-agendamiento exitoso            |
| Orden Cerrada en RR | 🟡 Naranja| Orden cerrada, no agendable        |
| ERROR               | 🔴 Rojo   | Error con detalle en la columna    |

---

## 🔧 Comandos útiles

```bash
# Ver logs en tiempo real
tail -f logs/celery.log
tail -f logs/error.log

# Reiniciar servicios
bash start.sh

# Ver workers activos
celery -A tareas.celery inspect active

# Detener todo
pkill -f "celery worker"
pkill -f "gunicorn"
```

---

## 🔒 Seguridad en producción

1. Cambia `SECRET_KEY` en config.py
2. Cambia la contraseña del admin tras el primer login
3. Configura Nginx como proxy reverso
4. Usa HTTPS con Let's Encrypt
5. Las contraseñas del módulo Claro se guardan en MySQL — considera cifrado adicional

### Nginx (opcional)

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
