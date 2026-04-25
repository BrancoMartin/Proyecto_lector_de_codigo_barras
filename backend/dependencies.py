from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from services.product_service import ProductService
from services.sale_service import SaleService
from services.ai_price_service import AIPriceService
from services.category_service import CategoryService
from services.attribute_service import AttributeService

def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    return ProductService(db)

def get_sale_service(db: Session = Depends(get_db)) -> SaleService:
    return SaleService(db)

def get_ai_service(db: Session = Depends(get_db)) -> AIPriceService:
    return AIPriceService(db)

def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    return CategoryService(db)

def get_attribute_service(db: Session = Depends(get_db)) -> AttributeService:
    return AttributeService(db)