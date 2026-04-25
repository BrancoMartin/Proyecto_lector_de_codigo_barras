
# from langchain_ollama import OllamaLLM  
from langchain_core.prompts import PromptTemplate  
from sqlalchemy.orm import Session  

from repositories.category_repository import CategoryRepository
from repositories.attribute_repository import AttributeRepository
from repositories.product_repository import ProductRepository
from models.product import Product
import json  
import re  
from langchain_groq import ChatGroq
from dotenv import load_dotenv

import os
load_dotenv()

class AIPriceService:
    
    
    def __init__(self, db: Session):
        
        self.db = db
        self.category = CategoryRepository(db)
        self.attribute = AttributeRepository(db)
        self.product = ProductRepository(db)
        
        
        try:
            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=os.environ.get("GROQ_API_KEY"),  
                temperature=0,
            )
        except Exception as e:
            print(f"Warning: Could not connect to Ollama: {e}")
            print("El sistema funcionará sin capacidades de IA hasta que Ollama esté disponible")
            self.llm = None
    
    
    
    def calculate_final_price(self, prompt: str, conversation_history: list):
        import json

        print("SERVICE")

        

        template = """
Eres un extractor de datos. Tu ÚNICA tarea es leer el mensaje del usuario, identificar a qué categoría se refiere y devolver un JSON válido.

LISTA DE CATEGORÍAS VÁLIDAS (base de datos):
{attribute}

REGLAS ESTRICTAS:
- Devolvé ÚNICAMENTE el JSON, sin texto previo, sin explicaciones, sin markdown, sin bloques de código.
- "attribute" debe ser EXACTAMENTE una de las palabras de la LISTA DE CATEGORÍAS VÁLIDAS de arriba. No inventes palabras.
- Si el usuario escribe una categoría con tilde, plural, mayúscula o parecida, igualmente buscá la más cercana en la lista.
- Si no encontrás ninguna categoría relacionada en la lista, devolvé: {{"attribute": null, "percentage": null}}
- "percentage" debe ser el número decimal del porcentaje.
  Ejemplos: 40% → 0.40 | 15% → 0.15 | 100% → 1.00

EJEMPLOS (asumiendo que la lista contiene: plastico, electronico, ropa, comida):
Entrada: "aumentame un 40% los productos de plastico"
Salida: {{"attribute": "plastico", "percentage": 0.40}}

Entrada: "subí un 20% la categoría electrónica"
Salida: {{"attribute": "electronico", "percentage": 0.20}}

Entrada: "quiero aumentar ropa un 15 por ciento"
Salida: {{"attribute": "ropa", "percentage": 0.15}}

Entrada: "aumentá un 10% los juguetes"
Salida: {{"attribute": null, "percentage": null}}

Historial de conversación: {conversation_history}
Mensaje del usuario: {prompt}

JSON:
"""

        result_prompt = PromptTemplate(
            input_variables=["prompt", "conversation_history"],
            template=template
        )

        chain = result_prompt | self.llm

        try:
            attribute = self.attribute.get_all()
            result = chain.invoke({
                "prompt": prompt,
                "conversation_history": conversation_history,
                "attribute": attribute
            })
            print("RESPONSE CALCULATE PRICE", result)

            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            attribute_name = data.get("attribute")
            percentage = data.get("percentage")

            print("NOMBRE DEL ATRIBUTO", attribute_name)

            products = self.product.get_products_by_name_attribute(attribute_name)
            
            print("PRODUCTOS", products)

            updated = []
            for p in products:
                new_price = round(p.price * (1 + percentage), 2)
                p.price = new_price
                saved = self.product.update(p)
                updated.append(saved)

            return {
                "success": True,
                "category": attribute_name,
                "percentage": percentage,
                "updated_products": len(updated)
            }

        except Exception as e:
            print(f"Error calculating price: {e}")
            return {"success": False, "error": str(e)}
       


    
    
            