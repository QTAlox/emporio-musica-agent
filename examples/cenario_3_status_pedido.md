# Scenario 3: Checking an Order and Redirecting an Accessory Request

### Customer

Pode verificar meu pedido 7? Também procuro palhetas Fender.

### Assistant

Consultei o pedido 7: ele consta como entregue. O código de rastreamento é BRKR1122334BR. Sobre as palhetas Fender, a loja trabalha somente com instrumentos musicais e não vende acessórios. Posso ajudar você a encontrar uma guitarra Fender, se quiser.

Tools used: `tool_get_order_status` looked up order 7 in the local order CSV. The assistant also follows the store's instrument-only scope when responding to the request for picks.

> Order information comes from the included sample data and is not connected to a live carrier.