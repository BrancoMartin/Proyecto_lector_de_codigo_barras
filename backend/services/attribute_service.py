
# from langchain_ollama import OllamaLLM  
from langchain_core.prompts import PromptTemplate  
from sqlalchemy.orm import Session  
from repositories.category_repository import CategoryRepository
from repositories.attribute_repository import AttributeRepository
from repositories.product_repository import ProductRepository
from models.attribute import Attribute
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()

class AttributeService:

    print("API KEY: ",os.environ.get("GROQ_API_KEY"))
    
    
    def __init__(self, db: Session):
        self.db = db
        self.category = CategoryRepository(db)
        self.attribute = AttributeRepository(db)
        self.product = ProductRepository(db)

         # Inicializamos Ollama con la nueva API de Langchain 1.x
        try:
            """
            self.llm = OllamaLLM(
                model="qwen2.5",  # EL LLM FINAL SERA QWEN2.5:0.5B POR QUE ES 100 GRATUITO, PERO PARA DESARROLLAR USARE Groq
                base_url="http://localhost:11434",  # URL del servidor Ollama
                # En Langchain 1.x ya no se usa callback_manager de la misma forma
            )
            """
            

            self.llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=os.environ.get("GROQ_API_KEY"),  
                temperature=0,
            )
            
        except Exception as e:
            # Si Ollama no está disponible, log y continuar sin IA
            print(f"Warning: Could not connect to Ollama: {e}")
            print("El sistema funcionará sin capacidades de IA hasta que Ollama esté disponible")
            self.llm = None
        

    def get_attributes(self):
                try: 
                    attributes = self.attribute.get_all()

                except Exception as e: 
                    return {
                        "error": str(e),
                        "success": False
                    }
                
                return attributes
    


    def create_attributes(self, product_name: str, product_description: str, product: object) -> list:
        import json

        categories = self.category.get_all()

        if not self.llm or not categories:
            return []

        # Convertir categorías a string legible para el prompt
        categories_str = ", ".join([c.category for c in categories])

        template = """
Eres un experto en catalogación de productos para e-commerce.

## Tarea
Dado un producto y una lista de categorías de atributos, generá exactamente UN atributo por categoría que describa al producto de forma precisa y coherente.

## Producto
- **Nombre:** {product_name}
- **Descripción:** {description}

## Categorías disponibles
{categories}

## Reglas estrictas
1. Cada atributo DEBE ser un valor válido y específico que pertenezca semánticamente a su categoría.
2. El atributo es el VALOR de la categoría, no una descripción del producto.
3. Respondé SOLO con el JSON, sin texto adicional ni markdown.

## Ejemplos correctos vs incorrectos
| Categoría | ✅ Correcto | ❌ Incorrecto |
|-----------|------------|--------------|
| Marca     | Nike       | Zapatilla deportiva |
| Material  | Cuero      | De buena calidad    |
| Color     | Rojo       | Producto rojo       |
| Talle     | 42         | Número de calzado   |

## Formato de respuesta
{{"attributes": [{{"attribute": "valor_especifico", "category_name": "nombre_categoria"}}]}}

JSON:
"""
        

        prompt = PromptTemplate(
            input_variables=["product_name", "categories", "description"],
            template=template
        )

        chain = prompt | self.llm

        try:
            result = chain.invoke({
                "product_name": product_name,
                "categories": categories_str,
                "description": product_description or ""
            })
            print("RESPONSE ATTRIBUTES", result)

            clean = result.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            attributes_data = data.get("attributes", [])

            print("ATRIBUTOS GENERADOS POR LA IA: ", attributes_data)
            
            for attr in attributes_data:
                # Buscar la categoría correspondiente
                category = next((c for c in categories if c.category == attr.get("category_name")), None)
                category_id = category.id if category else None

                amount_products = len(self.product.get_products_by_name_attribute(attr["attribute"]))

                print("AMOUNT PRODUCTS",amount_products)

                new_attribute = Attribute(
                    attribute=attr["attribute"],
                    category_id=category_id, 
                    amount_products=amount_products + 1
                )

                
                saved = self.attribute.create(new_attribute)

            return new_attribute

        except Exception as e:
            print(f"Error extracting attributes: {e}")
            return []

    

    def get_attributes_by_product(self, product_id: int): 
        try: 
            attributes = self.get_attributes_by_product(product_id)
        except Exception as e: 
            print(f"Error extracting attributes: {e}")
             
        return attributes    

    
