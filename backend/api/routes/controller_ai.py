from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.ai_price_service import AIPriceService
from services.category_service import CategoryService
from services.attribute_service import AttributeService
from dependencies import get_ai_service, get_category_service, get_attribute_service
from sqlalchemy.orm import Session


router = APIRouter()


class ConversationMessage(BaseModel):
    user_message: str
    conversation_history: list = []


@router.post("/chat_category/")
def chat_category(
    message: ConversationMessage,
    service: CategoryService = Depends(get_category_service)
):
    print("ENTRANDO A CREAR LAS CATEGORIAS")
 
    result = service.create_categories(
        message.user_message,
        message.conversation_history
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


# Calcula el precio en base al propt que ingreso el usuario. y lo hace en un barra distinta que 
# el que colocas al hacer las categorias


@router.put("/chat/")
def calculate_final_price(
    message: ConversationMessage,
    service: AIPriceService = Depends(get_ai_service)
):
    print("CONTROLLER")
    result = service.calculate_final_price(
        message.user_message,
        message.conversation_history
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.get("categories")
def get_categories(
    service: CategoryService = Depends(get_category_service)
):
    result = service.get_categories()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.get("attributes")
def get_attributes(
    service: AttributeService = Depends(get_attribute_service)
): 
    result = service.get_attributes()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.get("attributes/{id_product}")
def get_attributes_by_product(
    product_id: int,
    service: AttributeService = Depends(get_attribute_service)
): 
    result = service.get_attributes_by_product(product_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result
    
