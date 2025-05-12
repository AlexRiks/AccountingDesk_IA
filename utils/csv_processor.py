import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CSVProcessor:
    def __init__(self, date_format: str = "%Y-%m-%d"):
        """
        Inicializa el procesador de CSV.
        
        Args:
            date_format: Formato de fecha esperado en el CSV
        """
        self.date_format = date_format
        
    def validate_headers(self, df: pd.DataFrame) -> bool:
        """
        Valida que el CSV tenga las columnas requeridas.
        
        Args:
            df: DataFrame de pandas con los datos
            
        Returns:
            bool: True si las columnas son válidas
        """
        required_columns = ['fecha', 'descripcion', 'monto', 'producto']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Columnas faltantes en el CSV: {missing_columns}")
            return False
        return True
    
    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza los datos del CSV al formato esperado.
        
        Args:
            df: DataFrame de pandas con los datos
            
        Returns:
            DataFrame normalizado
        """
        try:
            # Convertir fechas
            df['fecha'] = pd.to_datetime(df['fecha'], format=self.date_format)
            
            # Normalizar montos (convertir a float y manejar diferentes formatos)
            df['monto'] = df['monto'].replace({',': '.'}, regex=True)
            df['monto'] = pd.to_numeric(df['monto'], errors='coerce')
            
            # Limpiar descripciones
            df['descripcion'] = df['descripcion'].str.strip()
            
            # Eliminar filas con valores nulos en campos críticos
            df = df.dropna(subset=['fecha', 'monto', 'descripcion'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error al normalizar datos: {str(e)}")
            raise
    
    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Procesa un archivo CSV y retorna una lista de transacciones.
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            Lista de diccionarios con las transacciones
        """
        try:
            # Leer CSV
            df = pd.read_csv(file_path)
            
            # Validar headers
            if not self.validate_headers(df):
                raise ValueError("El archivo CSV no tiene el formato correcto")
            
            # Normalizar datos
            df = self.normalize_data(df)
            
            # Convertir a lista de diccionarios
            transactions = df.to_dict('records')
            
            logger.info(f"Procesadas {len(transactions)} transacciones del CSV")
            return transactions
            
        except Exception as e:
            logger.error(f"Error al procesar archivo CSV {file_path}: {str(e)}")
            raise
    
    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Valida una transacción individual.
        
        Args:
            transaction: Diccionario con los datos de la transacción
            
        Returns:
            bool: True si la transacción es válida
        """
        required_fields = {
            'fecha': datetime,
            'descripcion': str,
            'monto': float,
            'producto': str
        }
        
        try:
            for field, field_type in required_fields.items():
                if field not in transaction:
                    return False
                if not isinstance(transaction[field], field_type):
                    return False
            return True
            
        except Exception as e:
            logger.error(f"Error al validar transacción: {str(e)}")
            return False 