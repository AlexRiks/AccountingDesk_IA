from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

def create_database():
    """
    Crea la base de datos y todas las tablas necesarias.
    """
    try:
        # Obtener configuración de la base de datos
        DB_HOST = os.getenv('DB_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME', 'accounting_desk')
        DB_USER = os.getenv('DB_USER', 'postgres')
        DB_PASSWORD = os.getenv('DB_PASSWORD', '')

        # Crear URL de conexión
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        # Crear engine
        engine = create_engine(DATABASE_URL)

        # Crear todas las tablas
        Base.metadata.create_all(engine)

        logger.info("Base de datos y tablas creadas exitosamente")

        # Crear sesión para insertar datos iniciales si es necesario
        Session = sessionmaker(bind=engine)
        session = Session()

        # Aquí puedes agregar código para insertar datos iniciales
        # Por ejemplo, categorías predefinidas

        session.commit()
        logger.info("Datos iniciales insertados correctamente")

    except Exception as e:
        logger.error(f"Error al crear la base de datos: {str(e)}")
        raise

if __name__ == "__main__":
    create_database() 