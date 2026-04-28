
from langchain_ollama import OllamaLLM  
from langchain_core.prompts import PromptTemplate  
from sqlalchemy.orm import Session  

from repositories.category_repository import CategoryRepository
from repositories.attribute_repository import AttributeRepository
from repositories.product_repository import ProductRepository
from models.product import Product
import json  
import re  
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
            self.llm = OllamaLLM(
                model="qwen2.5",  
                base_url="http://localhost:11434", 
            )
        except Exception as e:
            print(f"Warning: Could not connect to Ollama: {e}")
            print("El sistema funcionará sin capacidades de IA hasta que Ollama esté disponible")
            self.llm = None
    
    
    
    def calculate_final_price(self, prompt: str, conversation_history: list):
        import json

        print("SERVICE")

        

        template = """
Eres un extractor de datos JSON. Analizá el mensaje del usuario y devolvé ÚNICAMENTE un JSON.

ATRIBUTOS DISPONIBLES EN BASE DE DATOS (estos son los únicos valores válidos):
{attribute}

TAREA:
1. Buscá en el mensaje una palabra que coincida con algún ATRIBUTO de la lista (ignorando tildes, mayúsculas o plurales).
2. Extraé el porcentaje y convertilo a decimal (40% → 0.40).

REGLA CRÍTICA:
- El valor de "attribute" debe ser EXACTAMENTE una palabra de la lista de arriba.
- Si el usuario menciona algo que NO está en la lista, devolvé null.
- NO inventes, NO supongas, NO elijas el más parecido si no hay coincidencia clara.

FORMATO DE SALIDA (sin markdown, sin texto extra):
{{"attribute": "<atributo_exacto_o_null>", "percentage": <decimal_o_null>}}

EJEMPLOS (asumiendo lista: lego, samsung, plastico, metal):
Entrada: "aumentame 50% los productos de marca lego"  → {{"attribute": "lego", "percentage": 0.50}}
Entrada: "subí 20% los de samsung"                   → {{"attribute": "samsung", "percentage": 0.20}}
Entrada: "aumentá 40% los productos de plastico"     → {{"attribute": "plastico", "percentage": 0.40}}
Entrada: "quiero subir juguetes un 10%"              → {{"attribute": null, "percentage": null}}

Historial: {conversation_history}
Mensaje: {prompt}

JSON:
"""

        result_prompt = PromptTemplate(
            input_variables=["prompt", "conversation_history"],
            template=template
        )

        chain = result_prompt | self.llm

        try:
            attribute = self.attribute.get_all()
            print("ATRIBUTOS", attribute)
            result = chain.invoke({
                "prompt": prompt,
                "conversation_history": conversation_history,
                "attribute": attribute
            })
            print("RESPONSE CALCULATE PRICE", result)

            content = result.content

            clean = content.strip().replace("```json", "").replace("```", "").strip()
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
       


    
    
            