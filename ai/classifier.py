from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Tuple, Dict
import faiss
import json
import os
from datetime import datetime

class TransactionClassifier:
    def __init__(self, model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Inicializa el clasificador de transacciones.
        
        Args:
            model_name: Nombre del modelo de SentenceTransformers a utilizar
        """
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.categories = []
        self.embeddings = None
        
    def load_categories(self, categories_file: str) -> None:
        """
        Carga las categorías desde un archivo JSON y crea sus embeddings.
        
        Args:
            categories_file: Ruta al archivo JSON con las categorías
        """
        with open(categories_file, 'r', encoding='utf-8') as f:
            self.categories = json.load(f)
            
        # Crear embeddings para las categorías
        descriptions = [cat['description'] for cat in self.categories]
        self.embeddings = self.model.encode(descriptions)
        
        # Crear índice FAISS
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings.astype('float32'))
        
    def classify_transaction(self, description: str, k: int = 1) -> List[Tuple[str, float]]:
        """
        Clasifica una transacción basándose en su descripción.
        
        Args:
            description: Descripción de la transacción
            k: Número de categorías más cercanas a retornar
            
        Returns:
            Lista de tuplas (categoría, score de confianza)
        """
        # Crear embedding para la descripción
        query_vector = self.model.encode([description])
        
        # Buscar las k categorías más cercanas
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Convertir distancias a scores de confianza (1 - distancia normalizada)
        max_distance = np.max(distances)
        confidence_scores = 1 - (distances[0] / max_distance if max_distance > 0 else distances[0])
        
        # Retornar categorías y scores
        results = []
        for idx, score in zip(indices[0], confidence_scores):
            results.append((self.categories[idx]['name'], float(score)))
            
        return results
    
    def classify_dt_df(self, description: str, entities: List[str]) -> Tuple[str, float]:
        """
        Clasifica una transacción en términos de Due To / Due From.
        
        Args:
            description: Descripción de la transacción
            entities: Lista de entidades disponibles
            
        Returns:
            Tupla (clasificación DT/DF, score de confianza)
        """
        # Crear patrones para cada entidad
        patterns = []
        for entity in entities:
            patterns.extend([
                f"{entity} paid for",
                f"payment to {entity}",
                f"transfer to {entity}",
                f"received from {entity}"
            ])
        
        # Crear embeddings para los patrones
        pattern_embeddings = self.model.encode(patterns)
        
        # Crear embedding para la descripción
        query_vector = self.model.encode([description])
        
        # Calcular similitudes
        similarities = np.dot(query_vector, pattern_embeddings.T)[0]
        max_idx = np.argmax(similarities)
        confidence = float(similarities[max_idx])
        
        # Determinar la clasificación DT/DF
        pattern_idx = max_idx // 4
        is_payment = max_idx % 4 < 3
        entity = entities[pattern_idx]
        
        if is_payment:
            classification = f"{entity} DT"  # Due To
        else:
            classification = f"{entity} DF"  # Due From
            
        return classification, confidence
    
    def train_from_corrections(self, corrections: List[Dict]) -> None:
        """
        Actualiza el modelo con las correcciones de usuarios.
        
        Args:
            corrections: Lista de diccionarios con correcciones
                       {description: str, correct_category: str}
        """
        # Aquí se implementaría la lógica para fine-tuning del modelo
        # o actualización de embeddings basado en las correcciones
        pass 