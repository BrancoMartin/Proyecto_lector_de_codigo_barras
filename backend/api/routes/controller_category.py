from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dependencies import get_category_service
from services.category_service import CategoryService
from sqlalchemy.orm import Session
router = APIRouter()

class categoryValue(BaseModel):
    category:str

router.post("/")
def category(
    value: categoryValue,
    service: CategoryService = Depends(get_category_service)
):
    print("ENTRANDO A CREAR LAS CATEGORIAS")
 
    result = service.create_category_admin(
        value.category
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.get("/")
def get_categories(
    service: CategoryService = Depends(get_category_service)
):
    result = service.get_categories()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.get("/{id}")
def get_by_id(
    id: int, service: CategoryService = Depends(get_category_service)
):
    result = service.get_category(id)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.put("/{id}")
def update(id: int, service: CategoryService = Depends(get_category_service)):
    result = service.update(id)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@router.delete("/{id}")
def delete(id: int, service: CategoryService = Depends(get_category_service)):
    result = service.delete(id)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result