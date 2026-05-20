from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from services.category_service import CategoryService
from services.attribute_service import AttributeService
from services.ai_price_service import AIPriceService
from services.product_service import ProductService
from dependencies import get_category_service, get_attribute_service, get_ai_service, get_product_service
from dotenv import load_dotenv
from models.attribute_category import AttributeCategory
from models.attribute_value import AttributeValue
from models.product_attribute_bridge import ProductAttributeBridge
from models.product import Product
import os
import json
import re

from agent.model1_intent import detect_intent as new_detect_intent
from agent.model2a_create_product import create_product_with_attributes
from agent.model2b_price_type import detect_price_increase_type
from agent.model3_detect_attr import detect_category_and_value
from agent.model4_resolve_attr import resolve_attribute_in_db
from agent.model5_incomplete import handle_incomplete_info as new_handle_incomplete_info
from agent.model6_general import handle_general_query as new_handle_general_query

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
    message: str
    conversation_history: list = []
    context: dict = {}


class AgentResponse(BaseModel):
    message: str
    action_executed: str | None = None
    success: bool = True
    data: dict = {}


def get_llm():
    return OllamaLLM(
        model="qwen2.5:0.5b",
        base_url="http://localhost:11434",
    )


def detect_intent_legacy(message: str, llm=None) -> dict:
    if llm is None:
        llm = get_llm()

    template = """MENSAJE: "{user_message}"

INTENCIONES: crear_categoria, agregar_atributo, aumentar_precios, crear_productos, consulta_general

JSON:"""

    prompt = PromptTemplate(
        input_variables=["user_message"],
        template=template
    )

    chain = prompt | llm

    try:
        response = chain.invoke({"user_message": message})
        content = response.strip()
        clean = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return data
    except Exception as e:
        print(f"[LEGACY] Error detecting intent: {e}")
        return {"intent": "consulta_general", "confidence": 0.5}


@router.post("/chat", response_model=AgentResponse)
def agent_chat(
    chat_msg: ChatMessage,
    db: Session = Depends(get_db),
    category_service: CategoryService = Depends(get_category_service),
    attribute_service: AttributeService = Depends(get_attribute_service),
    ai_price_service: AIPriceService = Depends(get_ai_service),
    product_service: ProductService = Depends(get_product_service)
):
    try:
        user_message = chat_msg.message
        conversation_history = chat_msg.conversation_history or []
        context = chat_msg.context or {}

        llm = get_llm()

        intent_result = new_detect_intent(user_message)
        intent = intent_result.get("intent", "consulta_general")

        if not intent or intent == "info_incompleta":
            intent_result = detect_intent_legacy(user_message, llm)
            intent = intent_result.get("intent", "consulta_general")

        print(f"[AGENT] Intent: {intent} | Confidence: {intent_result.get('confidence', 0)}")

        if intent == "aumentar_precio":
            price_type_result = detect_price_increase_type(user_message)
            tipo = price_type_result.get("tipo")
            porcentaje = price_type_result.get("porcentaje")
            target = price_type_result.get("target")

            if not tipo or not porcentaje:
                return AgentResponse(
                    message="No entendi bien el aumento. ¿Que porcentaje queres aplicar y a que productos?",
                    action_executed="aumentar_precio",
                    success=False
                )

            if tipo == "todos":
                products = db.query(Product).all()
                updated = 0
                for p in products:
                    p.price = round(p.price * (1 + porcentaje / 100), 2)
                db.commit()
                updated = len(products)
                return AgentResponse(
                    message=f"✅ Se aumento el precio de TODOS los productos ({updated}) un {porcentaje}%",
                    action_executed="aumentar_precio",
                    success=True,
                    data={"updated_products": updated, "percentage": porcentaje}
                )

            elif tipo == "individual":
                products = db.query(Product).filter(Product.name.ilike(f"%{target}%")).all()
                if not products:
                    return AgentResponse(
                        message=f"No encontre ningun producto que se llame '{target}'.",
                        action_executed="aumentar_precio",
                        success=False
                    )
                updated = 0
                for p in products:
                    p.price = round(p.price * (1 + porcentaje / 100), 2)
                db.commit()
                updated = len(products)
                names = ", ".join([p.name for p in products])
                return AgentResponse(
                    message=f"✅ Se aumento el precio de '{names}' ({updated} producto(s)) un {porcentaje}%",
                    action_executed="aumentar_precio",
                    success=True,
                    data={"updated_products": updated, "percentage": porcentaje, "products": names}
                )

            elif tipo == "por_atributo":
                cats = db.query(AttributeCategory).all()
                existing_categories = [{"id": c.id, "name": c.name} for c in cats]

                attr_result = detect_category_and_value(target, existing_categories)
                categoria_inf = attr_result.get("categoria_inferida")
                valor = attr_result.get("valor")
                categoria_existe = attr_result.get("categoria_existe", False)

                if not categoria_inf:
                    return AgentResponse(
                        message=f"No pude determinar a que categoria pertenece '{target}'.",
                        action_executed="aumentar_precio",
                        success=False
                    )

                if not categoria_existe:
                    nueva_cat = AttributeCategory(name=categoria_inf)
                    db.add(nueva_cat)
                    db.commit()
                    db.refresh(nueva_cat)

                cat = db.query(AttributeCategory).filter(AttributeCategory.name == categoria_inf).first()
                if not cat:
                    cat = AttributeCategory(name=categoria_inf)
                    db.add(cat)
                    db.commit()
                    db.refresh(cat)

                attr_val = db.query(AttributeValue).filter(
                    AttributeValue.category_id == cat.id,
                    AttributeValue.value == valor
                ).first()
                if not attr_val:
                    attr_val = AttributeValue(category_id=cat.id, value=valor)
                    db.add(attr_val)
                    db.commit()
                    db.refresh(attr_val)

                bridges = db.query(ProductAttributeBridge).filter(
                    ProductAttributeBridge.attribute_value_id == attr_val.id
                ).all()
                product_ids = [b.product_id for b in bridges]

                if product_ids:
                    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
                    updated = 0
                    for p in products:
                        p.price = round(p.price * (1 + porcentaje / 100), 2)
                    db.commit()
                    updated = len(products)
                    return AgentResponse(
                        message=f"✅ Se aumento un {porcentaje}% a {updated} producto(s) con {categoria_inf} = {valor}",
                        action_executed="aumentar_precio",
                        success=True,
                        data={"updated_products": updated, "category": categoria_inf, "value": valor, "percentage": porcentaje}
                    )

                else:
                    all_products = db.query(Product).all()
                    productos_list = [
                        {"id": p.id, "name": p.name, "description": p.description or "", "price": p.price}
                        for p in all_products
                    ]
                    resolve_result = resolve_attribute_in_db(categoria_inf, valor, categoria_existe, productos_list)
                    if resolve_result.get("puede_inferir"):
                        detected_ids = resolve_result.get("productos_detectados", [])
                        if detected_ids:
                            products = db.query(Product).filter(Product.id.in_(detected_ids)).all()
                            for p in products:
                                bridge = ProductAttributeBridge(product_id=p.id, attribute_value_id=attr_val.id)
                                db.add(bridge)
                                p.price = round(p.price * (1 + porcentaje / 100), 2)
                            db.commit()
                            return AgentResponse(
                                message=f"✅ Se aumento un {porcentaje}% a {len(products)} producto(s) con {categoria_inf} = {valor}",
                                action_executed="aumentar_precio",
                                success=True,
                                data={"updated_products": len(products), "category": categoria_inf, "value": valor, "percentage": porcentaje}
                            )
                    return AgentResponse(
                        message=resolve_result.get("mensaje_usuario", f"No pude determinar que productos tienen {categoria_inf} = {valor}. ¿Podes indicarmelo?"),
                        action_executed="aumentar_precio",
                        success=False,
                        data={"context": {"intent": "aumentar_precio", "categoria": categoria_inf, "valor": valor, "porcentaje": porcentaje}}
                    )

            return AgentResponse(
                message="No pude procesar el aumento. Asegurate de incluir el porcentaje.",
                action_executed="aumentar_precio",
                success=False
            )

        elif intent == "crear_producto":
            cats = db.query(AttributeCategory).all()
            existing_categories = [{"id": c.id, "name": c.name} for c in cats]

            product_data = create_product_with_attributes(user_message, existing_categories)
            nombre = product_data.get("nombre")
            precio = product_data.get("precio")

            if not nombre:
                return AgentResponse(
                    message="No entendi el nombre del producto. ¿Podes repetirlo?",
                    action_executed="crear_producto",
                    success=False
                )

            if not precio:
                save_pending_product("default", product_data)
                return AgentResponse(
                    message=f"Producto: {nombre}\n\n¿Que precio tiene?",
                    action_executed="crear_producto",
                    success=True,
                    data={"product_data": product_data, "awaiting_price": True}
                )

            if re.match(r"^\d+$", user_message.strip()):
                pending = get_pending_product("default")
                if pending:
                    product_data = pending
                    product_data["barcode"] = user_message.strip()

            if "barcode" not in product_data or not product_data.get("barcode"):
                save_pending_product("default", product_data)
                return AgentResponse(
                    message=f"Datos del producto:\nNombre: {nombre}\nPrecio: ${precio}\n\nAhora escaneá o ingresá el codigo de barras.",
                    action_executed="crear_producto",
                    success=True,
                    data={"product_data": product_data}
                )

            try:
                result = product_service.create(
                    barcode=product_data["barcode"],
                    name=nombre,
                    price=float(precio),
                    description=product_data.get("descripcion")
                )
                if result:
                    atributos_inf = product_data.get("atributos_inferidos", [])
                    if atributos_inf:
                        for attr in atributos_inf:
                            cat_name = attr.get("categoria")
                            val = attr.get("valor")
                            if cat_name and val:
                                ac = db.query(AttributeCategory).filter(AttributeCategory.name == cat_name).first()
                                if not ac:
                                    ac = AttributeCategory(name=cat_name)
                                    db.add(ac)
                                    db.commit()
                                    db.refresh(ac)
                                av = db.query(AttributeValue).filter(
                                    AttributeValue.category_id == ac.id,
                                    AttributeValue.value == val
                                ).first()
                                if not av:
                                    av = AttributeValue(category_id=ac.id, value=val)
                                    db.add(av)
                                    db.commit()
                                    db.refresh(av)
                                bridge = ProductAttributeBridge(product_id=result.id, attribute_value_id=av.id)
                                db.add(bridge)
                        db.commit()

                    clear_pending_product("default")
                    return AgentResponse(
                        message=f"✅ Producto '{nombre}' creado exitosamente!",
                        action_executed="crear_producto",
                        success=True,
                        data=result
                    )
                else:
                    return AgentResponse(
                        message="❌ Error al crear el producto. Intenta de nuevo.",
                        action_executed="crear_producto",
                        success=False
                    )
            except Exception as e:
                return AgentResponse(
                    message=f"❌ Error al crear producto: {str(e)}",
                    action_executed="crear_producto",
                    success=False
                )

        elif intent == "crear_categoria":
            result = category_service.create_categories(user_message, conversation_history)
            if result.get("success"):
                return AgentResponse(
                    message=f"✅ Categorias creadas: {', '.join([c.get('category') for c in result.get('categories', [])])}",
                    action_executed="crear_categoria",
                    success=True,
                    data={"categories": result.get("categories", [])}
                )
            else:
                return AgentResponse(
                    message=f"❌ Error: {result.get('error')}",
                    action_executed="crear_categoria",
                    success=False
                )

        elif intent == "agregar_valor":
            result = attribute_service.create_attributes_from_prompt(user_message, conversation_history)
            if result.get("success"):
                return AgentResponse(
                    message=f"✅ Valores agregados a '{result.get('category')}': {', '.join([a.get('attribute') for a in result.get('attributes_created', [])])}",
                    action_executed="agregar_valor",
                    success=True,
                    data={"attributes": result.get("attributes_created", [])}
                )
            else:
                return AgentResponse(
                    message=f"❌ Error: {result.get('error')}",
                    action_executed="agregar_valor",
                    success=False
                )

        elif intent == "listar_categorias":
            cats = db.query(AttributeCategory).all()
            if cats:
                lines = ["**Categorias y valores disponibles:**\n"]
                for c in cats:
                    values = db.query(AttributeValue).filter(AttributeValue.category_id == c.id).all()
                    vals_str = ", ".join([v.value for v in values]) if values else "sin valores"
                    lines.append(f"• {c.name}: {vals_str}")
                return AgentResponse(
                    message="\n".join(lines),
                    action_executed="listar_categorias",
                    success=True,
                    data={"categories": [{"id": c.id, "name": c.name} for c in cats]}
                )
            else:
                categories_result = category_service.get_categories()
                if categories_result.get("success") and categories_result.get("categories"):
                    cat_list = categories_result["categories"]
                    if cat_list and hasattr(cat_list[0], '__dict__'):
                        cat_list = [{"id": c.id, "category": c.category} for c in cat_list]
                    message_content = "📋 **Categorias configuradas:**\n\n" + "\n".join([f"• {c.get('category', c)}" for c in cat_list])
                    return AgentResponse(
                        message=message_content,
                        action_executed="listar_categorias",
                        success=True,
                        data={"categories": cat_list}
                    )
                return AgentResponse(
                    message="No hay categorias configuradas. ¿Queres crear alguna?",
                    action_executed="listar_categorias",
                    success=True
                )

        elif intent == "info_incompleta":
            ctx = context or intent_result
            result = new_handle_incomplete_info(user_message, ctx)
            return AgentResponse(
                message=result.get("pregunta", "No entendi bien. ¿Podes darme mas detalles?"),
                action_executed="info_incompleta",
                success=True,
                data={"missing_field": result.get("campo_faltante"), "context": ctx}
            )

        else:
            total_products = db.query(Product).count()
            bridge_count = db.query(ProductAttributeBridge).count()
            avg_price = db.query(Product).with_entities(db.func.avg(Product.price)).scalar()
            min_price = db.query(Product).with_entities(db.func.min(Product.price)).scalar()
            max_price = db.query(Product).with_entities(db.func.max(Product.price)).scalar()

            cats = db.query(AttributeCategory).all()
            cat_stats = {}
            for c in cats:
                val_count = db.query(AttributeValue).filter(AttributeValue.category_id == c.id).count()
                cat_stats[c.name] = val_count

            db_stats = {
                "total_productos": total_products,
                "productos_sin_atributos": total_products - bridge_count if total_products > 0 else 0,
                "precio_promedio": round(avg_price, 2) if avg_price else 0,
                "precio_minimo": min_price if min_price else 0,
                "precio_maximo": max_price if max_price else 0,
                "categorias_y_valores": cat_stats
            }

            response = new_handle_general_query(user_message, db_stats)
            return AgentResponse(
                message=response,
                action_executed="consulta_general",
                success=True,
                data={"stats": db_stats}
            )

    except Exception as e:
        print(f"[ERROR] Agent: {e}")
        import traceback
        traceback.print_exc()
        return AgentResponse(
            message=f"❌ Ocurrio un error: {str(e)}",
            action_executed=None,
            success=False,
            data={"error": str(e)}
        )
