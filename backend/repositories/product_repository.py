from sqlalchemy.orm import Session
from models.product import Product
from models.category import Category
from models.attribute import Attribute


class ProductRepository:
    """Repository for product database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, product: Product) -> Product:
        """Creates a new product in the database"""
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_by_id(self, product_id: int) -> Product:
        """Gets a product by its ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_by_barcode(self, barcode: str) -> Product:
        """Gets a product by barcode"""
        return self.db.query(Product).filter(Product.barcode == barcode).first()
    
    def get_all(self) -> list[Product]:
        """Gets all products"""
        return self.db.query(Product).all()
    
    def update(self, product: Product) -> Product:
        """Updates product data"""
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete(self, product_id: int) -> bool:
        """Deletes a product"""
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            self.db.delete(product)
            self.db.commit()
            return True
        return False


    def get_products_by_category(self, category: Category):
        """Gets all products for a specific category"""
        products = self.db.query(Product).filter(Product.categories.any(id=category.id)).all()
        if not products:
            raise ValueError(f"No products found for category '{category.category}'")
        return products
        
    
    def get_products_by_attribute(self, attribute_id: int):
        print("GET PRODUCTS BY ATTRIBUTE")
        products = self.db.query(Product).filter(
            Product.attributes.any(Attribute.id == attribute_id)
        ).all()
    
        return products
    
    def get_products_by_name_attribute(self, name: str):  # ojo: debería ser str, no int
        print("Buscando por atributo:", name)
        
        # Primero verificá que el atributo existe
        attr = self.db.query(Attribute).filter(Attribute.attribute == name).first()
        print("Atributo encontrado:", attr)
        
        # Luego verificá que la relación existe
        products = self.db.query(Product).filter(
            Product.attributes.any(Attribute.attribute == name)
        ).all()
        
        print("Productos encontrados:", products)
        return products
