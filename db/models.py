from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Entidad(Base):
    __tablename__ = 'entidades'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    productos = relationship("Producto", back_populates="entidad")
    transacciones = relationship("Transaccion", back_populates="entidad")

class Producto(Base):
    __tablename__ = 'productos'
    
    id = Column(Integer, primary_key=True)
    entidad_id = Column(Integer, ForeignKey('entidades.id'))
    tipo = Column(String(50), nullable=False)  # Cuenta Bancaria, Tarjeta de Crédito
    nombre = Column(String(100), nullable=False)
    numero = Column(String(20))  # Últimos 4 dígitos o identificador
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    entidad = relationship("Entidad", back_populates="productos")
    transacciones = relationship("Transaccion", back_populates="producto")

class Categoria(Base):
    __tablename__ = 'categorias'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(500))
    categoria_padre_id = Column(Integer, ForeignKey('categorias.id'), nullable=True)
    
    subcategorias = relationship("Categoria")
    transacciones = relationship("Transaccion", back_populates="categoria")

class Transaccion(Base):
    __tablename__ = 'transacciones'
    
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, nullable=False)
    descripcion = Column(String(500), nullable=False)
    monto = Column(Float, nullable=False)
    entidad_id = Column(Integer, ForeignKey('entidades.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    clase = Column(String(100))  # DT/DF classification
    confianza_ia = Column(Float)  # AI confidence score
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    entidad = relationship("Entidad", back_populates="transacciones")
    producto = relationship("Producto", back_populates="transacciones")
    categoria = relationship("Categoria", back_populates="transacciones") 