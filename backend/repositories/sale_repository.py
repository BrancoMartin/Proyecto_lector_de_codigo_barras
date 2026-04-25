from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.sale import Sale
from models.sale_item import SaleItem
from models.product import Product
from datetime import datetime


class SaleRepository:
    """Repository for sale database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, sale: Sale) -> Sale:
        """Creates a new sale"""
        self.db.add(sale)
        self.db.commit()
        self.db.refresh(sale)
        return sale
    
    def get_by_id(self, sale_id: int) -> Sale:
        """Gets a sale by its ID"""
        return self.db.query(Sale).filter(Sale.id == sale_id).first()
    
    def get_all(self) -> list[Sale]:
        """Gets all sales ordered by date descending (most recent first)"""
        return self.db.query(Sale).order_by(desc(Sale.created_at)).all()
    
    def get_pending_sale(self) -> Sale:
        """Gets the most recent pending sale"""
        return self.db.query(Sale).filter(Sale.state == "pending").order_by(desc(Sale.created_at)).first()
    
    def add_item_to_sale(self, item: SaleItem) -> SaleItem:
        """Adds or updates an item in a sale"""
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def get_items(self, sale_id: int) -> list[SaleItem]:
        """Gets all items from a sale"""
        return self.db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    
    def get_item_by_sale_and_product(self, sale_id: int, product_id: int) -> SaleItem:
        """Gets a specific item from a sale by product"""
        return self.db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.product_id == product_id
        ).first()
    
    def update_total(self, sale: Sale) -> Sale:
        """Commits changes to a sale after updating total or state"""
        self.db.commit()
        self.db.refresh(sale)
        return sale
    
    def delete_item(self, sale_id: int, item_id: int) -> bool:
        """Deletes an item from a sale"""
        item = self.db.query(SaleItem).filter(
            SaleItem.sale_id == sale_id,
            SaleItem.id == item_id
        ).first()
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False
    
    def delete(self, sale_id: int) -> bool:
        """Deletes a sale and all its items"""
        self.db.query(SaleItem).filter(SaleItem.sale_id == sale_id).delete()
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if sale:
            self.db.delete(sale)
            self.db.commit()
            return True
        return False

    def get_item_by_id(self, item_id: int) -> SaleItem:
        """Gets a sale item by its ID"""
        return self.db.query(SaleItem).filter(SaleItem.id == item_id).first()
