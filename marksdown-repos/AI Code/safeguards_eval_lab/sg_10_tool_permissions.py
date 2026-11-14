"""SG-10  Least privilege for tools: deny by default, check role + validate arguments OUTSIDE the model.
Run: python sg_10_tool_permissions.py   (No LLM needed: we feed in tool calls a model might produce.)"""
from pydantic import BaseModel, Field, ValidationError

# 1) Which roles may use which tools. Anything not listed is DENIED.
ROLE_PERMISSIONS = {
    "customer": {"get_balance", "get_statement"},
    "support":  {"get_balance", "get_statement", "block_card"},
    "admin":    {"get_balance", "get_statement", "block_card", "refund"},
}

# 2) Argument schemas: types, ranges, formats. The model's arguments are untrusted input.
class GetBalanceArgs(BaseModel):
    account_id: str = Field(pattern=r"^ACC\d{6}$")

class RefundArgs(BaseModel):
    account_id: str = Field(pattern=r"^ACC\d{6}$")
    amount: float = Field(gt=0, le=5000)             # hard business limit, not up to the model

ARG_SCHEMAS = {"get_balance": GetBalanceArgs, "refund": RefundArgs}
OWNED_ACCOUNTS = {"customer-1": {"ACC123456"}}      # who owns what (the classic IDOR check)


def authorize_and_run(user_id: str, role: str, tool: str, args: dict) -> str:
    if tool not in ROLE_PERMISSIONS.get(role, set()):
        return f"DENIED: role '{role}' may not use '{tool}'"
    schema = ARG_SCHEMAS.get(tool)
    if schema:
        try:
            args = schema(**args).model_dump()
        except ValidationError as e:
            return f"REJECTED: bad arguments ({e.errors()[0]['loc'][0]}: {e.errors()[0]['msg']})"
    if role == "customer" and args.get("account_id") not in OWNED_ACCOUNTS.get(user_id, set()):
        return "DENIED: that account does not belong to you"       # prompt injection cannot bypass this
    return f"OK: executed {tool}({args})"


calls = [
    ("customer-1", "customer", "get_balance", {"account_id": "ACC123456"}),                 # legit
    ("customer-1", "customer", "refund",      {"account_id": "ACC123456", "amount": 100}),  # tool not allowed for role
    ("customer-1", "customer", "get_balance", {"account_id": "ACC999999"}),                 # someone else's account
    ("customer-1", "customer", "get_balance", {"account_id": "ACC1; DROP TABLE"}),          # malformed id
    ("admin-1",    "admin",    "refund",      {"account_id": "ACC123456", "amount": 90000}),# above the limit
    ("admin-1",    "admin",    "refund",      {"account_id": "ACC123456", "amount": 250}),  # legit
    ("customer-1", "customer", "delete_everything", {}),                                    # unknown tool
]
for user, role, tool, args in calls:
    print(f"{role:8} {tool:16} -> {authorize_and_run(user, role, tool, args)}")

print("\nGolden rule (OWASP): authorisation lives in YOUR code, never in the prompt. A system prompt that says")
print("'do not refund over 5000' is a wish. The le=5000 check above is a rule.")


"""
        USER / AI REQUESTS A TOOL
          e.g. refund ₹90,000
                    |
                    v
        +-----------------------+
        |  1. CHECK PERMISSIONS |
        |  Is this tool allowed |
        |  for this user's role?|
        +-----------------------+
                    |
             +------+------+
             |             |
          NOT ALLOWED    ALLOWED
             |             |
             v             v
          DENIED    +--------------------+
                   | 2. VALIDATE INPUTS  |
                   | Correct account ID?|
                   | Amount within limit?|
                   +--------------------+
                             |
                      +------+------+
                      |             |
                   INVALID        VALID
                      |             |
                      v             v
                  REJECTED   +------------------+
                             | 3. CHECK OWNERSHIP|
                             | Is it the user's |
                             | own account?     |
                             +------------------+
                                      |
                               +------+------+
                               |             |
                              NO            YES
                               |             |
                               v             v
                            DENIED      EXECUTE TOOL
"""