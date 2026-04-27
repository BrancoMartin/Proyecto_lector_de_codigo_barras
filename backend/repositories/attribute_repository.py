from sqlalchemy.orm import Session
from models.attribute import Attribute



class AttributeRepository: 
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, attribute: Attribute) -> Attribute:
        """Creates a new product in the database"""
        self.db.add(attribute)
        self.db.commit()
        self.db.refresh(attribute)
        return attribute
    
    def get_all(self):
        """Gets all attributes"""
        return self.db.query(Attribute).all()
    
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

    def update(self, attribute: Attribute) -> Attribute:
        """Updates an existing attribute in the database"""
        self.db.add(attribute)
        self.db.commit()
        self.db.refresh(attribute)
        return attribute