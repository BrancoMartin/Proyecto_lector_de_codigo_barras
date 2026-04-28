from sqlalchemy.orm import Session
from models.category import Category



class CategoryRepository: 
    def __init__(self, db: Session):
        self.db = db


    def get_categories_by_product(self, product_id: int, product_name):
        """Gets all categories for a specific product"""
        return self.db.query(Category).filter(Category.products.any(id=product_id)).all()


    def get_by_name(self, name):
        """Gets a category by name"""
        category = self.db.query(Category).filter(Category.category == name).first()
        if not category:
            raise ValueError(f"Category '{name}' not found")
        return category
        
   
