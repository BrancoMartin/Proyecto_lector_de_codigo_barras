"""
Controller dinámico que actúa como intermediario entre el frontend y los controllers específicos.
Detecta la intención del usuario usando LLM y ejecuta la acción correspondiente.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from services.category_service import CategoryService
from services.attribute_service import AttributeService
from services.ai_price_service import AIPriceService
from services.product_service import ProductService
from dependencies import get_category_service, get_attribute_service, get_ai_service, get_product_service
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

router = APIRouter()


_pending_products: dict = {}

def save_pending_product(session_id: str, product_data: dict):
    _pending_products[session_id] = product_data

def get_pending_product(session_id: str) -> dict | None:
    return _pending_products.get(session_id)

def clear_pending_product(session_id: str):
    _pending_products.pop(session_id, None)


class ChatMessage(BaseModel):
    """Modelo para los mensajes del chat"""
    message: str
    conversation_history: list = []


class AgentResponse(BaseModel):
    message: str
    action_executed: str | None = None  
    success: bool = True
    data: dict = {}


def get_llm():
    """Obtiene la instancia del LLM"""
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=os.environ.get("GROQ_API_KEY"),
    )


def detect_intent(message: str, conversation_history: list = None, llm=None) -> dict:
    
    
    if llm is None:
        llm = get_llm()
    
    if conversation_history is None:
        conversation_history = []
    
    # Construir contexto del historial
    context = "\n".join([
        f"Usuario: {msg.get('user', '')}\nAsistente: {msg.get('assistant', '')}"
        for msg in conversation_history[-4:]  # Últimos 4 mensajes para contexto
    ])
    
    template = """Eres un clasificador de intenciones. Devuelve ÚNICAMENTE un JSON.

INTENCIONES VÁLIDAS:
- crear_categoria: Crear nueva categoría (ej: "crear categoria material con plastico, metal")
- agregar_atributo: Agregar atributos a categoría existente (ej: "agregar madera a material")
- modificar_categoria: Cambiar nombres de categorías o atributos
- aumentar_precios: Aumentar precios (ej: "aumenta 20% los precios de samsung")
- listar_categorias: Ver categorías actuales (ej: "que categorias hay")
- crear_productos: Crear un producto con nombre y precio (ej: "creame una pelota a $500") O cuando el mensaje es solo una secuencia de números (ej: "7790895000109")
- consulta_general: Pregunta general sobre finanzas o negocios
- informacion_incompleta: Falta información para ejecutar una acción

CONTEXTO: {context}
MENSAJE: "{user_message}"

REGLAS:
1. Acción concreta → devolvé esa intención.
2. Solo números → siempre "crear_productos".
3. Pregunta general → "consulta_general".
4. SOLO JSON, sin markdown.

FORMATO:
{{"intent": "nombre_intención", "confidence": 0.95, "reasoning": "breve explicación"}}

JSON:"""
    
    prompt = PromptTemplate(
        input_variables=["user_message", "context"],
        template=template
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "user_message": message,
            "context": context if context else "Conversación nueva"
        })
        
        content = response.content.strip()
        # Limpiar markdown y códigos si están presentes
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        
        return data
    except Exception as e:
        print(f"Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5, "error": str(e)}


@router.post("/chat", response_model=AgentResponse)
def agent_chat(
    chat_msg: ChatMessage,
    db: Session = Depends(get_db),
    category_service: CategoryService = Depends(get_category_service),
    attribute_service: AttributeService = Depends(get_attribute_service),
    ai_price_service: AIPriceService = Depends(get_ai_service),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Endpoint principal del agente dinámico.
    Recibe un mensaje, detecta intención y ejecuta la acción correspondiente.
    """
    
    try:
        llm = get_llm()
        user_message = chat_msg.message
        conversation_history = chat_msg.conversation_history or []
        
        # 1. Detectar intención
        intent_result = detect_intent(user_message, conversation_history, llm)
        intent = intent_result.get("intent", "consulta_general")
        
        print(f"[AGENT] Intent detected: {intent}")
        
        # 2. Ejecutar acción según intención
        
        if intent == "crear_categoria":
            result = category_service.create_categories(user_message, conversation_history)
            if result.get("success"):
                return AgentResponse(
                    message=f"✅ Se crearon exitosamente las siguientes categorías: {', '.join([c.get('category') for c in result.get('categories', [])])}\n\nAhora puedes decirme qué atributos tiene cada categoría o pedir un aumento de precios.",
                    action_executed="crear_categoria",
                    success=True,
                    data={"categories": result.get("categories", [])}
                )
            else:
                return AgentResponse(
                    message=f"❌ Error al crear categorías: {result.get('error')}",
                    action_executed="crear_categoria",
                    success=False,
                    data={"error": result.get("error")}
                )
        
        elif intent == "aumentar_precios":
            result = ai_price_service.calculate_final_price(user_message, conversation_history)
            if result.get("success"):
                return AgentResponse(
                    message=f"✅ Se aumentaron {result.get('updated_products', 0)} productos de '{result.get('category')}' un {result.get('percentage', 0)*100:.0f}%",
                    action_executed="aumentar_precios",
                    success=True,
                    data={
                        "category": result.get("category"),
                        "percentage": result.get("percentage"),
                        "updated_products": result.get("updated_products")
                    }
                )
            else:
                return AgentResponse(
                    message=f"❌ No puedo aumentar precios: {result.get('error')}\n\nProbablemente la categoría especificada no existe o no tiene atributos configurados. ¿Quieres crear una categoría primero?",
                    action_executed="aumentar_precios",
                    success=False,
                    data={"error": result.get("error")}
                )
        
        
        elif intent == "agregar_atributo":
            result = attribute_service.create_attributes_from_prompt(user_message, conversation_history)
            if result.get("success"):
                attrs_created = ", ".join([a.get("attribute") for a in result.get("attributes_created", [])])
                return AgentResponse(
                    message=f"✅ Se agregaron los siguientes atributos a '{result.get('category')}': {attrs_created}\n\nAhora puedes usar estos atributos para aumentar precios.",
                    action_executed="agregar_atributo",
                    success=True,
                    data={"attributes": result.get("attributes_created", [])}
                )
            else:
                return AgentResponse(
                    message=f"❌ No pude agregar los atributos: {result.get('error')}\n\nAsegúrate de mencionar la categoría correcta.",
                    action_executed="agregar_atributo",
                    success=False,
                    data={"error": result.get("error")}
                )
        
        elif intent == "listar_categorias": 
            categories = category_service.get_categories()
            attributes = attribute_service.get_attributes()
            
            if categories.get("success") and attributes.get("success"):
                cat_list = categories.get("categories", categories.get("data", []))
                attr_list = attributes.get("attributes", attributes.get("data", []))
                
                # Convertir a diccionarios si es necesario
                if cat_list and hasattr(cat_list[0], '__dict__'):
                    cat_list = [{"id": c.id, "category": c.category} for c in cat_list]
                if attr_list and hasattr(attr_list[0], '__dict__'):
                    attr_list = [{"id": a.id, "attribute": a.attribute, "category_id": a.category_id} for a in attr_list]
                
                message_content = "📋 **Categorías configuradas:**\n\n"
                if cat_list:
                    for cat in cat_list:
                        cat_name = cat.get('category', cat) if isinstance(cat, dict) else cat
                        cat_id = cat.get('id', None) if isinstance(cat, dict) else None
                        message_content += f"• {cat_name}\n"
                        # Filtrar atributos de esta categoría
                        cat_attrs = [a for a in attr_list if isinstance(a, dict) and a.get('category_id') == cat_id]
                        if cat_attrs:
                            for attr in cat_attrs:
                                message_content += f"  - {attr.get('attribute', attr)}\n"
                else:
                    message_content += "Sin categorías configuradas aún.\n"
                
                return AgentResponse(
                    message=message_content + "\n¿Quieres agregar más categorías o atributos?",
                    action_executed="listar_categorias",
                    success=True,
                    data={"categories": cat_list, "attributes": attr_list}
                )
            else:
                return AgentResponse(
                    message="No pude cargar las categorías. Intenta de nuevo.",
                    action_executed="listar_categorias",
                    success=False
                )
            
        elif intent == "informacion_incompleta":
            # Hacer preguntas al usuario para completar la información
            questions = generate_clarification_questions(user_message, llm)
            return AgentResponse(
                message=questions,
                action_executed="informacion_incompleta",
                success=True,
                data={}
            )
        elif intent == "crear_productos":
            try:
                # Verificar si el mensaje es un barcode (solo números)
                if re.match(r"^\d+$", user_message.strip()):
                    pending = get_pending_product("default")
                    
                    if not pending:
                        return AgentResponse(
                            message="No tengo ningún producto pendiente. Primero decime el nombre y precio del producto.",
                            action_executed="crear_productos",
                            success=False
                        )
                    
                    pending = get_pending_product("default")
                    result = product_service.create(
                        barcode=user_message.strip(),
                        name=pending["nombre"],
                        price=float(pending["precio"]),
                        description=pending.get("descripcion")  
                    )
                    clear_pending_product("default")

                    print("RESULTADO DE LA CREACION", result)
                    
                    if result:
                        return AgentResponse(
                            message=f"✅ Producto '{pending['nombre']}' creado exitosamente con el código {user_message.strip()}!",
                            action_executed="crear_productos",
                            success=True,
                            data=result
                        )
                    else:
                        return AgentResponse(
                            message=f"❌ Error al crear el producto: {result.get('error')}",
                            action_executed="crear_productos",
                            success=False,
                            data={"error": result.get("error")}
                        )
                
                else:
                    # Extraer nombre, precio y descripción del mensaje con el LLM
                    template = """Extrae los datos del producto del mensaje del usuario. Devolvé ÚNICAMENTE un JSON válido.

                    Mensaje: "{user_message}"

                    REGLAS:
                    - "nombre": el nombre del producto
                    - "precio": solo el número, sin símbolos (ej: 30000)
                    - "descripcion": si la menciona, sino null

                    FORMATO (sin markdown, sin código, solo JSON):
                    {{"nombre": "nombre del producto", "precio": 999.99, "descripcion": null}}

                    JSON:"""

                    prompt = PromptTemplate(
                        input_variables=["user_message"],
                        template=template
                    )

                    chain = prompt | llm
                    response = chain.invoke({"user_message": user_message})

                    print("RESPUESTA DE LA IA EN EL CREATE PRODUCT", response)

                    content = response.content.strip().replace("```json", "").replace("```", "").strip()
                    product_data = json.loads(content)
                    
                    save_pending_product("default", product_data)

                    desc_text = f"Descripción: {product_data.get('descripcion')}\n" if product_data.get("descripcion") else ""

                    return AgentResponse(
                        message=f"Perfecto! Tengo los datos del producto:\n"
                                f"Nombre: {product_data['nombre']}\n"
                                f"Precio: ${product_data['precio']}\n"
                                f"{desc_text}"
                                f"\nAhora escaneá o ingresá el código de barras para crear el producto.",
                        action_executed="crear_productos",
                        success=True,
                        data=product_data
                    )
            
            except Exception as e:
                return AgentResponse(
                    message=f"❌ Error al procesar el producto: {str(e)}",
                    action_executed="crear_productos",
                    success=False,
                    data={"error": str(e)}
                )
        
        else:  # consulta_general o sin intención clara
            # Responder como asesor financiero
            response = financial_advisor_response(user_message, conversation_history, llm)
            return AgentResponse(
                message=response,
                action_executed=None,
                success=True,
                data={}
            )
         
    except Exception as e:
        print(f"[ERROR] Agent chat error: {e}")
        import traceback
        traceback.print_exc()
        return AgentResponse(
            message=f"❌ Ocurrió un error: {str(e)}",
            action_executed=None,
            success=False,
            data={"error": str(e)}
        )


def generate_clarification_questions(user_message: str, llm) -> str:
    """Genera preguntas de clarificación cuando falta información"""
    
    template = """El usuario intentó hacer algo pero falta información. 
Haz preguntas claras y amigables para obtener los datos faltantes.

Mensaje: "{user_message}"

Responde como un asesor amigable, haz preguntas específicas y directas.
Sin markdown, texto plano, máximo 3-4 líneas."""
    
    prompt = PromptTemplate(
        input_variables=["user_message"],
        template=template
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"user_message": user_message})
        return response.content
    except Exception as e:
        return f"Necesito más información. ¿Qué categoría o atributo quieres modificar?"


def financial_advisor_response(user_message: str, conversation_history: list = None, llm=None) -> str:
    """Genera una respuesta como asesor financiero para consultas generales"""
    
    if llm is None:
        llm = get_llm()
    
    if conversation_history is None:
        conversation_history = []
    
    context = "\n".join([
        f"Usuario: {msg.get('user', '')}\nAsistente: {msg.get('assistant', '')}"
        for msg in conversation_history[-3:]
    ])
    
    template = """Eres un asesor financiero amigable que ayuda a pequeños negocios con estrategias de precios, márgenes y gestión de inventario.

CONTEXTO:
{context}

USUARIO PREGUNTA: "{user_message}"

Responde de forma clara, práctica y amigable. Máximo 3-4 párrafos. 
Sugiere acciones concretas si es posible (ej: "prueba aumentar un 15% en categorías de mayor demanda").
Sin markdown, texto plano."""
    
    prompt = PromptTemplate(
        input_variables=["user_message", "context"],
        template=template
    )
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "user_message": user_message,
            "context": context if context else "Conversación nueva"
        })
        return response.content
    except Exception as e:
        return "No puedo procesar esa pregunta en este momento. Intenta nuevamente."
