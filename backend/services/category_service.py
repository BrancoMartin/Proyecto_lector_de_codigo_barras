
from langchain_ollama import OllamaLLM  
from langchain_core.prompts import PromptTemplate  
from sqlalchemy.orm import Session  
from repositories.category_repository import CategoryRepository
from repositories.attribute_repository import AttributeRepository
from repositories.product_repository import ProductRepository
from models.category import Category
from dotenv import load_dotenv
import os
load_dotenv()


class CategoryService:
    
    
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
        

    def get_category(self, category_id: int):
                try: 
                    category = self.category.get_by_id(category_id)

                except Exception as e: 
                    return {
                        "error": str(e),
                        "success": False
                    }
                
                return category
    

    def get_categories(self):
        try: 
            categories = self.category.get_all()
            return {
                "success": True,
                "categories": categories
            }

        except Exception as e: 
            return {
                "error": str(e),
                "success": False
            }
    


    
        
    
    def create_categories(self, user_message: str, conversation_history: list = None) -> dict:
        import json

        print("ENTRANDO AL SERVICE DE CREAR LAS CATEGORIAS", user_message)

        if not self.llm:
            print("ENTRANDO AL NOT SELF.LLM")
            return {"error": "AI service not available"}

        if conversation_history is None:
            conversation_history = []

        context = "\n".join([
            f"Usuario: {msg['user']}\nAsistente: {msg['assistant']}"
            for msg in conversation_history
        ])

        template = """
    Eres un asistente que ayuda a crear categorias de aumento de precio.
    El usuario te va a describir cómo aumentan sus precios y vos tenés que devolver ÚNICAMENTE un JSON con las categorías a crear.

    {context}

    Usuario: {user_message}

    Respondé ÚNICAMENTE con un JSON válido, sin texto adicional, sin explicaciones, sin markdown, sin bloques de código, en español, sin acentos y en minuscula.
    El formato debe ser exactamente este:
    {{"categories": [{{"category": "nombre_categoria"}}, {{"category": "otra_categoria"}}]}}

    JSON:
    """

        prompt = PromptTemplate(
            input_variables=["context", "user_message"],
            template=template
        )

        chain = prompt | self.llm

        try:
            print("ENTRANDO A EJECUTAR LA CADENA")
            response = chain.invoke({
                "context": context if context else "Conversación nueva",
                "user_message": user_message
            })
            print("RESPONSE", response)

            content = response.content

            clean = content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            categories = data.get("categories", [])

            result = []
            for cat in categories:
                nueva_categoria = Category(category=cat["category"])
                created = self.category.create(nueva_categoria)
                result.append({"id": created.id, "category": created.category})

            return {
                "success": True,
                "categories": result
            }

        except Exception as e:
            print("ENTRANDO A LA EXCEPTION", e)
            return {
                "error": str(e),
                "success": False
            }
        

    def create_category_admin(self, category: str):
        cate = Category(category)

        result = self.category.create(cate)

        if not result: 
            Exception("Category could not be created")
        
        return result
    
    def update(self, id: int):
        try: 
            response = self.category.update(id)
            return {
                "success": True, 
                "message": "Category updated successfully"
            }
        except Exception as e: 
            return {
                "success": False, 
                "error": str(e)
            }