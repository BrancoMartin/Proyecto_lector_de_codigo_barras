from sqlalchemy.orm import Session
from models.category import Category
from repositories.repository_base import RepositoryBase



class CategoryRepository(RepositoryBase[Category]): 
    def __init__(self, db: Session):
        super().__init__(db, Category)
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
        
   
