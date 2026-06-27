"""MCP tool: fetch a user's orders. [EVAL FIXTURE: contains a planted bug]"""

# Input schema advertised to the model (the contract).
INPUT_SCHEMA = {
    "type": "object",
    "properties": {"user_id": {"type": "string"}},
    "required": ["user_id"],
}


def handle(args: dict) -> list:
    # Drift: the handler reads `userId`, but the schema advertises `user_id`.
    # The producer (model, guided by the schema) and consumer disagree on the key.
    uid = args["userId"]
    return db_lookup_orders(uid)
