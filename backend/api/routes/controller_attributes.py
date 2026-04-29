from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dependencies import get_attribute_service
from services.attribute_service import AttributeService
from sqlalchemy.orm import Session
router = APIRouter()

class attributeValue(BaseModel):
    category:str
    category_id: int
    amount_products: int



@router.get("/")
def get_attributes(
    service: AttributeService = Depends(get_attribute_service)
): 
    result = service.get_attributes()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.get("/{id_attribute}")
def get_attributes_by_id(
    attribute_id: int,
    service: AttributeService = Depends(get_attribute_service)
): 
    result = service.get_by_id(attribute_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result




@router.post("/")
def create_attribute(
    value: attributeValue,
    service: AttributeService = Depends(get_attribute_service)
):
    try: 
        result = service.create(value)
    except Exception as e: 
        raise f"error, {e}"
    return result

@router.put("/{id_attribute}")
def update(
    id_attribute: int,
    service: AttributeService = Depends(get_attribute_service)
): 
    try: 
        result = service.update(id_attribute)
        
    except Exception as e: 
        raise f"error, {e}"
    return result


@router.delete("/{id_attribute}")
def delete(
    id_attribute: int,
    service: AttributeService = Depends(get_attribute_service)
): 
    try: 
        result = service.delete(id_attribute)
    except Exception as e: 
        raise f"error, {e}"
    
    return result


@router.get("/{id_product}")
def get_attributes_by_product(
    product_id: int,
    service: AttributeService = Depends(get_attribute_service)
): 
    result = service.get_attributes_by_product(product_id)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result