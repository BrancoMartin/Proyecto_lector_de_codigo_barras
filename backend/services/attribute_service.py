from langchain_ollama import OllamaLLM  
from langchain_core.prompts import PromptTemplate  
from sqlalchemy.orm import Session  
from repositories.category_repository import CategoryRepository
from repositories.attribute_repository import AttributeRepository
from repositories.product_repository import ProductRepository
from models.attribute import Attribute
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
        
            self.llm = OllamaLLM(
                model="qwen2.5",  
                base_url="http://localhost:11434", 
            )
            
            
        except Exception as e:
            # Si Ollama no está disponible, log y continuar sin IA
            print(f"Warning: Could not connect to Ollama: {e}")
            print("El sistema funcionará sin capacidades de IA hasta que Ollama esté disponible")
            self.llm = None
        

    def get_attributes(self):
        try: 
            attributes = self.attribute.get_all()
            return {
                "success": True,
                "attributes": attributes
            }

        except Exception as e: 
            return {
                "error": str(e),
                "success": False
            }
    


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


La palabra que me devuelvas tiene que ser toda en minuscula y sin tildes.
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

            for item in attributes_data:  
                attribute_value = item['attribute']
                category_name = item['category_name']

                # Buscar la categoría correspondiente
                category = next((c for c in categories if c.category == category_name), None) 
                category_id = category.id if category else None

                existing_attribute = self.attribute.get_by_name(attribute_value)

                if existing_attribute:
                    print("ATTRIBUTE", existing_attribute)
                    existing_attribute.amount_products += 1
                    try:
                        self.attribute.update(existing_attribute)
                        product.attributes.append(existing_attribute)
                    except Exception as e:
                        return f'error al querer actualizar la cantidad de productos: {e}'  
                else:
                    new_attribute = Attribute(
                        attribute=attribute_value,  
                        category_id=category_id,
                        amount_products=1
                    )
                    saved = self.attribute.create(new_attribute)
                    product.attributes.append(saved)

                    if not saved:
                        return f'error al querer crear un atributo: {e}' 

            return attributes_data  

        except Exception as e:
            print(f"Error extracting attributes: {e}")
            return []

    

    def get_attributes_by_product(self, product_id: int): 
        try: 
            attributes = self.attribute.get_attributes_by_product(product_id)
        except Exception as e: 
            print(f"Error getting attributes: {e}")
             
        return attributes

    def create_attribute_for_category(self, attribute_name: str, category_id: int) -> dict:
        """
        Crea un atributo para una categoría específica.
        Usado cuando el usuario quiere agregar atributos al chat.
        """
        try:
            # Verificar que la categoría existe
            category = self.category.get_all()
            cat_found = next((c for c in category if c.id == category_id), None)
            
            if not cat_found:
                return {"success": False, "error": f"Categoría con ID {category_id} no existe"}
            
            # Verificar si el atributo ya existe
            existing = self.attribute.get_by_name(attribute_name)
            if existing and existing.category_id == category_id:
                return {"success": False, "error": f"El atributo '{attribute_name}' ya existe en esta categoría"}
            
            # Crear el atributo
            new_attribute = Attribute(
                attribute=attribute_name,
                category_id=category_id,
                amount_products=0
            )
            created = self.attribute.create(new_attribute)
            
            return {
                "success": True,
                "attribute": {
                    "id": created.id,
                    "attribute": created.attribute,
                    "category_id": created.category_id
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_attributes_from_prompt(self, user_message: str, conversation_history: list = None) -> dict:
        """
        Crea atributos basados en un prompt del usuario.
        Ejemplo: "Quiero agregar los atributos Samsung, LG a la categoria marca"
        """
        import json
        
        if not self.llm:
            return {"success": False, "error": "LLM no disponible"}
        
        if conversation_history is None:
            conversation_history = []
        
        # Obtener categorías existentes
        categories = self.category.get_all()
        if not categories:
            return {"success": False, "error": "No hay categorías disponibles"}
        
        categories_str = ", ".join([c.category for c in categories])
        
        template = """Eres un asistente que extrae información para crear atributos.
        
CATEGORÍAS DISPONIBLES: {categories}

TAREA: El usuario quiere agregar atributos. Extrae:
1. El nombre de la categoría
2. La lista de atributos a agregar

MENSAJE: "{user_message}"

Responde SOLO con JSON sin explicaciones:
{{"category": "nombre_categoria", "attributes": ["attr1", "attr2", "attr3"]}}

JSON:"""
        
        prompt = PromptTemplate(
            input_variables=["user_message", "categories"],
            template=template
        )
        
        chain = prompt | self.llm
        
        try:
            response = chain.invoke({
                "user_message": user_message,
                "categories": categories_str
            })
            
            content = response.content.strip()
            clean = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            
            category_name = data.get("category")
            attributes_list = data.get("attributes", [])
            
            # Buscar la categoría
            category = next((c for c in categories if c.category.lower() == category_name.lower()), None)
            if not category:
                return {"success": False, "error": f"Categoría '{category_name}' no encontrada"}
            
            # Crear atributos
            created = []
            for attr_name in attributes_list:
                result = self.create_attribute_for_category(attr_name.lower(), category.id)
                if result.get("success"):
                    created.append(result.get("attribute"))
            
            return {
                "success": True,
                "category": category.category,
                "attributes_created": created
            }
        
        except Exception as e:
            print(f"Error creating attributes from prompt: {e}")
            return {"success": False, "error": str(e)}

