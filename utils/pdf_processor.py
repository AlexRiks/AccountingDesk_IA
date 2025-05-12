import pytesseract
from pdf2image import convert_from_path
from typing import List, Dict, Any
import re
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, tesseract_path: str = None):
        """
        Inicializa el procesador de PDF.
        
        Args:
            tesseract_path: Ruta al ejecutable de Tesseract OCR
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrae texto de un archivo PDF usando OCR.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            str: Texto extraído del PDF
        """
        try:
            # Convertir PDF a imágenes
            images = convert_from_path(pdf_path)
            
            # Extraer texto de cada página
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image, lang='spa')
            
            return text
            
        except Exception as e:
            logger.error(f"Error al extraer texto del PDF {pdf_path}: {str(e)}")
            raise
            
    def parse_transactions(self, text: str) -> List[Dict[str, Any]]:
        """
        Parsea transacciones del texto extraído.
        
        Args:
            text: Texto extraído del PDF
            
        Returns:
            Lista de diccionarios con las transacciones
        """
        transactions = []
        
        # Patrones para extraer información
        # Estos patrones deben ajustarse según el formato específico de los PDFs
        date_pattern = r'\d{2}/\d{2}/\d{4}'
        amount_pattern = r'\$?\s*[\d,]+\.\d{2}'
        
        # Dividir por líneas y procesar cada una
        lines = text.split('\n')
        for line in lines:
            try:
                # Buscar fecha
                date_match = re.search(date_pattern, line)
                if not date_match:
                    continue
                    
                # Buscar monto
                amount_match = re.search(amount_pattern, line)
                if not amount_match:
                    continue
                    
                # Extraer descripción (todo lo que está entre fecha y monto)
                date_end = date_match.end()
                amount_start = amount_match.start()
                description = line[date_end:amount_start].strip()
                
                if description:
                    transaction = {
                        'fecha': datetime.strptime(date_match.group(), '%d/%m/%Y'),
                        'descripcion': description,
                        'monto': float(amount_match.group().replace('$', '').replace(',', '')),
                        'producto': 'PENDIENTE'  # Se debe determinar según el contexto
                    }
                    transactions.append(transaction)
                    
            except Exception as e:
                logger.warning(f"Error al procesar línea: {line}. Error: {str(e)}")
                continue
                
        return transactions
        
    def process_file(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Procesa un archivo PDF y extrae las transacciones.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Lista de diccionarios con las transacciones
        """
        try:
            # Extraer texto del PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Parsear transacciones del texto
            transactions = self.parse_transactions(text)
            
            logger.info(f"Procesadas {len(transactions)} transacciones del PDF")
            return transactions
            
        except Exception as e:
            logger.error(f"Error al procesar archivo PDF {pdf_path}: {str(e)}")
            raise
            
    def validate_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Valida una transacción extraída del PDF.
        
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