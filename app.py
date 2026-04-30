import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, join_room
from werkzeug.utils import secure_filename
from datetime import datetime

from config import Config
from models import db, Usuario, Trabajo, OrdenResultado

app = Flask(__name__)
app.config.from_object(Config)

# ── Extensiones ──
db.init_app(app)
socketio = SocketIO(app, message_queue=Config.REDIS_URL, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor inicia sesión para continuar."

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)

EXTENSIONES_PERMITIDAS = {"xlsx", "xls"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ─────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = Usuario.query.filter_by(username=request.form["username"]).first()
        if user and user.activo and user.check_password(request.form["password"]):
            login_user(user, remember=True)
            return redirect(url_for("dashboard"))
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ─────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────
@app.route("/")
@login_required
def dashboard():
    trabajos = Trabajo.query.filter_by(usuario_id=current_user.id)\
                            .order_by(Trabajo.creado_en.desc()).limit(20).all()
    return render_template("dashboard.html", trabajos=trabajos)


# ─────────────────────────────────────────────────────
# SUBIR EXCEL Y LANZAR TAREA
# ─────────────────────────────────────────────────────
@app.route("/subir", methods=["POST"])
@login_required
def subir_excel():
    if "excel" not in request.files:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("dashboard"))

    archivo = request.files["excel"]
    if archivo.filename == "" or not allowed_file(archivo.filename):
        flash("Archivo inválido. Solo se permiten .xlsx o .xls", "error")
        return redirect(url_for("dashboard"))

    # Verificar que el usuario tenga credenciales del módulo Claro
    if not current_user.claro_user or not current_user.claro_pass:
        flash("Configura tus credenciales del módulo Claro primero.", "error")
        return redirect(url_for("perfil"))

    nombre = secure_filename(archivo.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_guardado = f"{current_user.id}_{timestamp}_{nombre}"
    ruta = os.path.join(Config.UPLOAD_FOLDER, nombre_guardado)
    archivo.save(ruta)

    # Crear registro en BD
    trabajo = Trabajo(
        usuario_id=current_user.id,
        nombre_excel=nombre,
        estado="pendiente"
    )
    db.session.add(trabajo)
    db.session.commit()

    # Lanzar tarea Celery
    from tareas import ejecutar_agendamiento
    task = ejecutar_agendamiento.delay(
        trabajo.id, ruta,
        current_user.claro_user,
        current_user.claro_pass
    )
    trabajo.task_id = task.id
    db.session.commit()

    flash(f"✅ Tarea iniciada — procesando {nombre}", "success")
    return redirect(url_for("ver_trabajo", trabajo_id=trabajo.id))


# ─────────────────────────────────────────────────────
# VER TRABAJO / PROGRESO
# ─────────────────────────────────────────────────────
@app.route("/trabajo/<int:trabajo_id>")
@login_required
def ver_trabajo(trabajo_id):
    trabajo = Trabajo.query.filter_by(
        id=trabajo_id, usuario_id=current_user.id
    ).first_or_404()
    ordenes = OrdenResultado.query.filter_by(trabajo_id=trabajo_id)\
                                  .order_by(OrdenResultado.procesado_en.desc()).all()
    return render_template("trabajo.html", trabajo=trabajo, ordenes=ordenes)


@app.route("/api/trabajo/<int:trabajo_id>")
@login_required
def api_trabajo(trabajo_id):
    trabajo = Trabajo.query.filter_by(
        id=trabajo_id, usuario_id=current_user.id
    ).first_or_404()
    ordenes = [o.to_dict() for o in
               OrdenResultado.query.filter_by(trabajo_id=trabajo_id).all()]
    data = trabajo.to_dict()
    data["ordenes"] = ordenes
    return jsonify(data)


# ─────────────────────────────────────────────────────
# DESCARGAR RESULTADO
# ─────────────────────────────────────────────────────
@app.route("/descargar/<int:trabajo_id>")
@login_required
def descargar(trabajo_id):
    trabajo = Trabajo.query.filter_by(
        id=trabajo_id, usuario_id=current_user.id
    ).first_or_404()
    if not trabajo.archivo_salida:
        flash("El archivo de resultados aún no está disponible.", "error")
        return redirect(url_for("ver_trabajo", trabajo_id=trabajo_id))
    return send_from_directory(
        Config.OUTPUT_FOLDER,
        trabajo.archivo_salida,
        as_attachment=True,
        download_name=f"resultado_{trabajo.nombre_excel}"
    )


# ─────────────────────────────────────────────────────
# PERFIL / CREDENCIALES CLARO
# ─────────────────────────────────────────────────────
@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        if request.form.get("claro_user"):
            current_user.claro_user = request.form["claro_user"]
            current_user.claro_pass = request.form["claro_pass"]
            db.session.commit()
            flash("✅ Credenciales del módulo Claro actualizadas.", "success")
        if request.form.get("new_password"):
            current_user.set_password(request.form["new_password"])
            db.session.commit()
            flash("✅ Contraseña actualizada.", "success")
    return render_template("perfil.html")


# ─────────────────────────────────────────────────────
# ADMIN — gestión de usuarios
# ─────────────────────────────────────────────────────
@app.route("/admin/usuarios")
@login_required
def admin_usuarios():
    if not current_user.es_admin:
        flash("Acceso denegado.", "error")
        return redirect(url_for("dashboard"))
    usuarios = Usuario.query.order_by(Usuario.creado_en.desc()).all()
    return render_template("admin_usuarios.html", usuarios=usuarios)


@app.route("/admin/usuarios/crear", methods=["POST"])
@login_required
def crear_usuario():
    if not current_user.es_admin:
        return jsonify({"error": "No autorizado"}), 403
    data = request.get_json()
    if Usuario.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Usuario ya existe"}), 400
    u = Usuario(
        username=data["username"],
        email=data["email"],
        es_admin=data.get("es_admin", False)
    )
    u.set_password(data["password"])
    db.session.add(u)
    db.session.commit()
    return jsonify({"ok": True, "id": u.id})


@app.route("/admin/usuarios/<int:uid>/toggle", methods=["POST"])
@login_required
def toggle_usuario(uid):
    if not current_user.es_admin:
        return jsonify({"error": "No autorizado"}), 403
    u = Usuario.query.get_or_404(uid)
    u.activo = not u.activo
    db.session.commit()
    return jsonify({"activo": u.activo})


# ─────────────────────────────────────────────────────
# LIMPIAR HISTORIAL
# ─────────────────────────────────────────────────────
@app.route("/limpiar_historial", methods=["POST"])
@login_required
def limpiar_historial():
    trabajos = Trabajo.query.filter_by(usuario_id=current_user.id).all()
    for t in trabajos:
        OrdenResultado.query.filter_by(trabajo_id=t.id).delete()
        db.session.delete(t)
    db.session.commit()
    flash("✅ Historial limpiado.", "success")
    return redirect(url_for("dashboard"))


# ─────────────────────────────────────────────────────
# PIN 2FA — recibir PIN del usuario y guardarlo en Redis
# ─────────────────────────────────────────────────────
@app.route("/api/pin/<int:trabajo_id>", methods=["POST"])
@login_required
def recibir_pin(trabajo_id):
    trabajo = Trabajo.query.filter_by(
        id=trabajo_id, usuario_id=current_user.id
    ).first_or_404()
    data = request.get_json()
    pin = (data or {}).get("pin", "").strip()
    if not pin:
        return jsonify({"error": "PIN vacío"}), 400
    import redis
    from config import Config
    r = redis.from_url(Config.REDIS_URL)
    r.setex(f"pin_trabajo_{trabajo_id}", 120, pin)  # expira en 2 min
    return jsonify({"ok": True})


# ─────────────────────────────────────────────────────
# DETENER TRABAJO
# ─────────────────────────────────────────────────────
@app.route("/api/detener/<int:trabajo_id>", methods=["POST"])
@login_required
def detener_trabajo(trabajo_id):
    trabajo = Trabajo.query.filter_by(
        id=trabajo_id, usuario_id=current_user.id
    ).first_or_404()
    if trabajo.estado not in ("ejecutando", "pendiente"):
        return jsonify({"error": "El trabajo no está en ejecución"}), 400
    import redis
    from config import Config
    r = redis.from_url(Config.REDIS_URL)
    r.setex(f"detener_trabajo_{trabajo_id}", 600, "1")
    trabajo.estado = "detenido"
    db.session.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────────────
# REANUDAR TRABAJO
# ─────────────────────────────────────────────────────
@app.route("/api/reanudar/<int:trabajo_id>", methods=["POST"])
@login_required
def reanudar_trabajo(trabajo_id):
    trabajo = Trabajo.query.filter_by(
        id=trabajo_id, usuario_id=current_user.id
    ).first_or_404()
    if trabajo.estado != "detenido":
        return jsonify({"error": "El trabajo no está detenido"}), 400
    import redis
    from config import Config
    # Limpiar señal de detener
    r = redis.from_url(Config.REDIS_URL)
    r.delete(f"detener_trabajo_{trabajo_id}")
    # Buscar el archivo original
    import glob
    patron = os.path.join(Config.UPLOAD_FOLDER, f"{trabajo.usuario_id}_*_{trabajo.nombre_excel}")
    archivos = sorted(glob.glob(patron))
    if not archivos:
        return jsonify({"error": "No se encontró el archivo Excel original"}), 404
    task = ejecutar_agendamiento.delay(
        trabajo.id, archivos[-1],
        usuario.claro_user, usuario.claro_pass
    )
    trabajo.task_id = task.id
    trabajo.estado = "ejecutando"
    db.session.commit()
    return jsonify({"ok": True})


# ─────────────────────────────────────────────────────
# SOCKET.IO — unirse a sala de progreso
# ─────────────────────────────────────────────────────
@socketio.on("suscribir")
def on_suscribir(data):
    trabajo_id = data.get("trabajo_id")
    join_room(f"trabajo_{trabajo_id}")


# ─────────────────────────────────────────────────────
# INIT DB
# ─────────────────────────────────────────────────────
@app.cli.command("init-db")
def init_db():
    """Crea las tablas y el usuario admin inicial."""
    db.create_all()
    if not Usuario.query.filter_by(username="admin").first():
        admin = Usuario(username="admin", email="admin@empresa.com", es_admin=True)
        admin.set_password("Admin123!")
        db.session.add(admin)
        db.session.commit()
        print("✅ BD creada. Admin: admin / Admin123!")
    else:
        print("✅ BD ya existe.")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
