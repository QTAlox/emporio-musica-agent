import json
from typing import Any, Dict, List, Optional
from groq import Groq

from src.config import GROQ_API_KEY, MODEL_NAME
from src.tools import (
    tool_search_products,
    tool_search_promotions,
    tool_get_order_status,
    tool_check_store_policy,
)

SYSTEM_INSTRUCTION = """
You are Empório da Música's customer-support assistant in Campo Grande/MS.
Always reply in natural, friendly, professional Brazilian Portuguese.
The store sells musical instruments only, not accessories (strings, picks, cables, cases, pedals, or amps).
Use tools for exact product, order, and policy facts; never invent them.
Politely decline unrelated requests and redirect to musical instruments.
Avoid Markdown tables. For product searches, show up to three relevant options as concise bullet points with the name, price, and stock. Do not show internal product IDs or unnecessary descriptions.
For questions about current promotions or discounts, always use the promotion search tool. Report the discounted price only when the tool provides it; if no matching active promotions are found, say so plainly.
For a single-product price question, answer directly in one or two sentences instead of listing a table.
Keep the answer complete and concise, and finish with a helpful follow-up question when appropriate.
Do not use Markdown bold markers (**); write responses in plain text.
"""


def _clean_response(text: str) -> str:
    return text.replace("**", "").strip()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tool_search_products",
            "description": "Search the instrument catalog by name or maximum price. For promotions and discounts, use tool_search_promotions instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": ["string", "null"],
                        "description": "Optional product name or description. Use null when omitted.",
                    },
                    "max_price": {
                        "type": ["number", "null"],
                        "description": "Optional maximum price. Use null when no price limit is specified.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_search_promotions",
            "description": "Search active discounts and promotions. Use this for any question about products on sale or current offers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_name": {
                        "type": ["string", "null"],
                        "description": "Optional instrument category, such as Guitarras or Violões. Use null if no category is specified.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_get_order_status",
            "description": "Get a store order's status and items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order identifier."},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_check_store_policy",
            "description": "Search official store policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Policy question or topic to search."},
                },
                "required": ["query"],
            },
        },
    },
]


class EmporioAgent:

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or GROQ_API_KEY
        if not key:
            raise ValueError("API key is missing. Set GROQ_API_KEY in your environment or .env file.")

        self.client = Groq(api_key=key)
        self.model = MODEL_NAME
        self.tools_map = {
            "tool_search_products": tool_search_products,
            "tool_search_promotions": tool_search_promotions,
            "tool_get_order_status": tool_get_order_status,
            "tool_check_store_policy": tool_check_store_policy
        }

    def _get_tools_definition(self) -> List[Dict[str, Any]]:
        return TOOLS

    def chat(
        self,
        user_message: str,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tool_results: List[Dict[str, Any]] = []
        for _ in range(3):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_tools_definition(),
                tool_choice="auto",
                parallel_tool_calls=False,
                temperature=0.2,
                max_completion_tokens=512,
            )
            assistant_message = response.choices[0].message
            if not assistant_message.tool_calls:
                return _clean_response(assistant_message.content or "")

            messages.append(assistant_message.model_dump(exclude_none=True))
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                if tool_name not in self.tools_map:
                    raise ValueError(f"Model requested unknown tool: {tool_name}")

                arguments = json.loads(tool_call.function.arguments)
                if not isinstance(arguments, dict):
                    raise TypeError(f"Arguments for {tool_name} must be a JSON object.")

                tool_result = self.tools_map[tool_name](**arguments)
                tool_results.append({
                    "tool": tool_name,
                    "result": tool_result,
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str),
                })

        final_messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "Responda em português brasileiro natural, de forma amigável e concisa, usando "
                    "somente a conversa e os resultados das ferramentas fornecidos. Não use tabelas "
                    "Markdown, não mostre IDs internos de produtos e não tente chamar ferramentas. "
                    "Para buscas de produtos, use até três tópicos com nome, preço e estoque. "
                    "Entregue uma resposta completa."
                ),
            }
        ]
        if history:
            final_messages.extend(
                {"role": item["role"], "content": item["content"][:1000]}
                for item in history[-4:]
                if item.get("role") in {"user", "assistant"}
                and isinstance(item.get("content"), str)
            )
        final_messages.extend([
            {"role": "user", "content": user_message},
            {
                "role": "user",
                "content": "Resultados confirmados: " + json.dumps(
                    tool_results,
                    ensure_ascii=False,
                    default=str,
                ),
            },
        ])
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=final_messages,
            temperature=0.2,
            max_completion_tokens=512,
        )
        final_text = final_response.choices[0].message.content
        if not final_text:
            raise RuntimeError("The model returned no final answer after using tools.")
        return _clean_response(final_text)