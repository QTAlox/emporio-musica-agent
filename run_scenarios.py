import random

import pandas as pd

from src.agent import EmporioAgent
from src.config import BASE_DIR


SCENARIOS = [
    {
        "id": 1,
        "queries": [
            "Quais violões custam até R$ 1000?",
            "Pode indicar violões disponíveis por no máximo mil reais?",
            "Estou procurando um violão barato, até R$ 1000. O que tem?",
        ],
        "tool": "tool_search_products",
    },
    {
        "id": 2,
        "queries": [
            "Me arrependi da compra. Como funciona a devolução?",
            "Comprei um produto e quero devolver. Qual é a política da loja?",
            "Ainda posso pedir reembolso de uma compra?",
        ],
        "tool": "tool_check_store_policy",
    },
    {
        "id": 3,
        "queries": [
            "Qual é o status do pedido 3? E vocês vendem palhetas Fender?",
            "Pode verificar meu pedido 7? Também procuro palhetas Fender.",
            "Meu pedido número 18 já foi enviado? Vocês têm palhetas da Fender?",
        ],
        "tool": "tool_get_order_status",
    },
]


def main() -> None:
    agent = EmporioAgent()
    results = []

    for scenario in SCENARIOS:
        query = random.choice(scenario["queries"])
        response = agent.chat(query)
        results.append(
            {
                "scenario_id": scenario["id"],
                "customer_query": query,
                "expected_tool": scenario["tool"],
                "agent_response": response,
            }
        )

    output_path = BASE_DIR / "final_results.csv"
    pd.DataFrame(results).to_csv(output_path, index=False)
    print(f"Execution completed. Output saved to {output_path}")


if __name__ == "__main__":
    main()
