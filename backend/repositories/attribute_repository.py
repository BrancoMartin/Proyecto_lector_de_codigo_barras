from sqlalchemy.orm import Session
from models.attribute import Attribute



class AttributeRepository: 
    def __init__(self, db: Session):
        self.db = db
    
    def get_attributes_by_product(self, product_id): 
        attributes = self.db.query(Attribute).filter(
            Attribute.products.any(id=product_id)
        ).all()
        return attributes

    def get_by_name(self, name): 
        print("GET ATTRIBUTE BY NAME")
        attribute = self.db.query(Attribute).filter(
            Attribute.attribute == name
        ).first()
        return attribute
