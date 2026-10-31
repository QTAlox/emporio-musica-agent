import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import DATA_DIR

class DatabaseManager:
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.products = pd.read_csv(self.data_dir / "products.csv")
        self.promotions = pd.read_csv(self.data_dir / "promotions.csv")
        self.categories = pd.read_csv(self.data_dir / "categories.csv")
        self.customers = pd.read_csv(self.data_dir / "customers.csv")
        self.orders = pd.read_csv(self.data_dir / "orders.csv")
        self.order_items = pd.read_csv(self.data_dir / "order_items.csv")

    def search_products(
        self, 
        query: Optional[str] = None, 
        max_price: Optional[float] = None, 
        category_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        df = self.products.copy()
        
        if max_price is not None:
            df = df[df["price_brl"] <= max_price]
            
        if query:
            df = df[
                df["name"].str.contains(query, case=False, na=False) | 
                df["description"].str.contains(query, case=False, na=False)
            ]

        if category_name:
            category_ids = self.categories.loc[
                self.categories["name"].str.contains(category_name, case=False, na=False),
                "category_id",
            ]
            df = df[df["category_id"].isin(category_ids)]
            
        return df.to_dict(orient="records")

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        order = self.orders[self.orders["order_id"].astype(str) == str(order_id)]
        if order.empty:
            return {"error": "Order not found."}
        
        items = self.order_items[self.order_items["order_id"].astype(str) == str(order_id)]
        return {
            "order": order.to_dict(orient="records")[0],
            "items": items.to_dict(orient="records")
        }

    def search_active_promotions(
        self, category_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        active_promotions = self.promotions[
            self.promotions["is_active"].astype(bool)
        ]
        products = self.products[self.products["status"] == "active"]
        matches = active_promotions.merge(
            products,
            on="product_id",
            how="inner",
            suffixes=("_promotion", "_product"),
        )
        matches = matches.merge(
            self.categories[["category_id", "name"]],
            on="category_id",
            how="left",
            suffixes=("", "_category"),
        )

        if category_name:
            category_ids = self.categories.loc[
                self.categories["name"].str.contains(
                    category_name, case=False, na=False
                ),
                "category_id",
            ]
            matches = matches[matches["category_id"].isin(category_ids)]

        matches["promotion_price_brl"] = (
            matches["price_brl"]
            * (1 - matches["discount_percent"] / 100)
        ).round(2)
        return matches[
            [
                "product_id",
                "name",
                "name_category",
                "price_brl",
                "discount_percent",
                "promotion_price_brl",
                "stock_quantity",
                "description_promotion",
            ]
        ].rename(
            columns={
                "name_category": "category",
                "description_promotion": "promotion_name",
            }
        ).to_dict(orient="records")