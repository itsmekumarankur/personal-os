"""
07 DATA GUARDRAILS  -  "the agent must never know more than the person it serves"

Biggest real-world agent leak: the agent has a powerful service account, and a clever question makes it
reveal someone else's data. So enforce access control BELOW the model, in code, using the END USER's identity:
  1. ROW-LEVEL     a customer sees only their own rows; an RM only assigned customers
  2. COLUMN MASKING PAN / email masked unless role + purpose justify full view
  3. PURPOSE        compliance may see everything only for purpose='audit' (and that is logged)
  4. RAG ACL        filter retrieved documents by permission BEFORE they enter the prompt
                    (a document the user cannot read must never be given to the model)
  5. MINIMISATION   give the model only the fields it needs for the question

Run: python 07_data_guardrails.py
"""
from dataclasses import dataclass

CUSTOMERS = [
    {"id": "C1", "name": "Asha Rao",  "pan": "ABCDE1234F", "email": "asha@mail.com",  "rm": "RM1", "value": 1_200_000},
    {"id": "C2", "name": "Vikram Jain", "pan": "PQRST5678Z", "email": "vik@mail.com", "rm": "RM2", "value": 8_400_000},
    {"id": "C3", "name": "Neha Iyer", "pan": "LMNOP9012K", "email": "neha@mail.com",  "rm": "RM1", "value": 450_000},
]
DOCS = [
    {"text": "Public: how SIPs work",                     "roles": {"customer", "rm", "support", "compliance"}, "owner": None},
    {"text": "Internal: RM commission grid",              "roles": {"rm", "compliance"},                          "owner": None},
    {"text": "Asha's KYC review notes",                   "roles": {"customer", "rm", "compliance"},              "owner": "C1"},
    {"text": "Vikram's complaint escalation",             "roles": {"customer", "rm", "compliance"},              "owner": "C2"},
]


@dataclass
class Principal:
    user_id: str
    role: str
    purpose: str = "service"


def mask_pan(v):
    return v[:2] + "******" + v[-2:]


def mask_email(v):
    return v[0] + "***@" + v.split("@")[1]


def visible_rows(p):
    if p.role == "customer":
        return [c for c in CUSTOMERS if c["id"] == p.user_id]
    if p.role == "rm":
        return [c for c in CUSTOMERS if c["rm"] == p.user_id]
    if p.role == "support":
        return CUSTOMERS                                    # may look up anyone, but masked below
    if p.role == "compliance" and p.purpose == "audit":
        print("      (audit-purpose access recorded in the audit log)")
        return CUSTOMERS
    return []


def shape(row, p, fields):
    allowed = {"customer": {"name", "pan", "email", "value"}, "rm": {"name", "pan", "email", "value"},
               "support": {"name", "email"}, "compliance": {"name", "pan", "email", "value"}}[p.role]
    out = {}
    for f in fields:                                          # minimisation: only requested AND permitted
        if f not in allowed:
            out[f] = "<no access>"
        elif f == "pan":
            out[f] = row[f] if (p.role == "customer" or (p.role == "compliance" and p.purpose == "audit")) else mask_pan(row[f])
        elif f == "email" and p.role == "support":
            out[f] = mask_email(row[f])
        else:
            out[f] = row[f]
    return out


def query_customers(p, fields):
    return [shape(r, p, fields) for r in visible_rows(p)]


def retrieve_docs(p, owner_context=None):
    """RAG: permission filter applied to retrieved chunks BEFORE prompt construction."""
    ok = []
    for d in DOCS:
        if p.role not in d["roles"]:
            continue
        if d["owner"] and p.role == "customer" and d["owner"] != p.user_id:
            continue
        ok.append(d["text"])
    return ok


if __name__ == "__main__":
    people = [Principal("C1", "customer"), Principal("RM1", "rm"), Principal("S9", "support"),
              Principal("CO1", "compliance"), Principal("CO1", "compliance", "audit")]
    print('The agent is asked: "show me every customer\'s name, PAN, email and portfolio value"\n')
    for p in people:
        print(f"* {p.role} {p.user_id} (purpose={p.purpose})")
        rows = query_customers(p, ["name", "pan", "email", "value"])
        for r in rows or ["<no rows>"]:
            print("     ", r)
    print("\nRAG retrieval for the question 'what do we know about complaints and KYC?'")
    for p in (Principal("C1", "customer"), Principal("C2", "customer"), Principal("S9", "support"), Principal("RM1", "rm")):
        print(f"* {p.role} {p.user_id}: {retrieve_docs(p)}")
    print("\nTakeaway: the model never sees data the user could not see, so no prompt trick can leak it.")
