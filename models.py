from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    es_admin   = db.Column(db.Boolean, default=False)
    activo     = db.Column(db.Boolean, default=True)
    creado_en  = db.Column(db.DateTime, default=datetime.utcnow)
    # Credenciales del módulo Claro (encriptadas)
    claro_user = db.Column(db.String(120))
    claro_pass = db.Column(db.String(256))

    trabajos   = db.relationship("Trabajo", backref="usuario", lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<Usuario {self.username}>"


class Trabajo(db.Model):
    __tablename__ = "trabajos"
    id            = db.Column(db.Integer, primary_key=True)
    usuario_id    = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    task_id       = db.Column(db.String(64), unique=True)   # Celery task ID
    nombre_excel  = db.Column(db.String(256))
    estado        = db.Column(db.String(32), default="pendiente")
    # pendiente | ejecutando | completado | error
    total         = db.Column(db.Integer, default=0)
    procesadas    = db.Column(db.Integer, default=0)
    exitosas      = db.Column(db.Integer, default=0)
    fallidas      = db.Column(db.Integer, default=0)
    archivo_salida = db.Column(db.String(256))
    creado_en     = db.Column(db.DateTime, default=datetime.utcnow)
    terminado_en  = db.Column(db.DateTime)

    ordenes       = db.relationship("OrdenResultado", backref="trabajo", lazy=True)

    def to_dict(self):
        return {
            "id":            self.id,
            "task_id":       self.task_id,
            "nombre_excel":  self.nombre_excel,
            "estado":        self.estado,
            "total":         self.total,
            "procesadas":    self.procesadas,
            "exitosas":      self.exitosas,
            "fallidas":      self.fallidas,
            "archivo_salida": self.archivo_salida,
            "creado_en":     self.creado_en.strftime("%Y-%m-%d %H:%M") if self.creado_en else None,
            "terminado_en":  self.terminado_en.strftime("%Y-%m-%d %H:%M") if self.terminado_en else None,
        }


class OrdenResultado(db.Model):
    __tablename__ = "ordenes_resultado"
    id            = db.Column(db.Integer, primary_key=True)
    trabajo_id    = db.Column(db.Integer, db.ForeignKey("trabajos.id"), nullable=False)
    numero_orden  = db.Column(db.String(32))
    tipo_orden    = db.Column(db.String(64))
    estado        = db.Column(db.String(64))   # AGENDADO | RE-AGENDADO | ERROR | Orden Cerrada en RR
    detalle       = db.Column(db.String(512))
    procesado_en  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "numero_orden": self.numero_orden,
            "tipo_orden":   self.tipo_orden,
            "estado":       self.estado,
            "detalle":      self.detalle,
            "procesado_en": self.procesado_en.strftime("%Y-%m-%d %H:%M:%S") if self.procesado_en else None,
        }
