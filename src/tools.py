from typing import Dict, Any, Optional
from src.database import DatabaseManager
from src.rag import PolicyRAG

db_manager = DatabaseManager()
policy_rag = PolicyRAG()


def tool_search_products(query: Optional[str] = None, max_price: Optional[float] = None) -> Dict[str, Any]:
    matches = db_manager.search_products(query=query, max_price=max_price)
    results = [
        {
            "product_id": product["product_id"],
            "name": product["name"],
            "price_brl": product["price_brl"],
            "stock_quantity": product["stock_quantity"],
            "description": str(product["description"])[:100],
        }
        for product in matches[:3]
    ]
    return {"results": results, "count": len(matches), "showing": len(results)}


def tool_search_promotions(category_name: Optional[str] = None) -> Dict[str, Any]:
    matches = db_manager.search_active_promotions(category_name=category_name)
    results = [
        {
            "name": promotion["name"],
            "category": promotion["category"],
            "price_brl": promotion["price_brl"],
            "discount_percent": promotion["discount_percent"],
            "promotion_price_brl": promotion["promotion_price_brl"],
            "stock_quantity": promotion["stock_quantity"],
            "promotion_name": promotion["promotion_name"],
        }
        for promotion in matches[:3]
    ]
    return {"results": results, "count": len(matches), "showing": len(results)}


def tool_get_order_status(order_id: str) -> Dict[str, Any]:
    return db_manager.get_order_status(order_id=order_id)

def tool_check_store_policy(query: str) -> Dict[str, Any]:
    policy_text = policy_rag.search_policies(query=query)
    return {"policy_info": policy_text[:1200]}