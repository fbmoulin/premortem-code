"""MCP tool: fetch a user's orders. [EVAL FIXTURE: correct]"""

# Input schema advertised to the model (the contract).
INPUT_SCHEMA = {
    "type": "object",
    "properties": {"user_id": {"type": "string"}},
    "required": ["user_id"],
}


def handle(args: dict) -> list:
    # Handler reads the same key the schema declares — producer and consumer agree.
    uid = args["user_id"]
    return db_lookup_orders(uid)
