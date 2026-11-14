"""SG-11  Guarding an LLM-written SQL tool: read-only, one statement, table allowlist, row cap.
Run: python sg_11_sql_guard.py   (No LLM needed.)"""
import re, sqlite3

ALLOWED_TABLES = {"products", "orders"}
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|pragma|replace|truncate|vacuum|load_extension)\b", re.I)


def validate_sql(sql: str) -> tuple[bool, str]:
    s = sql.strip().rstrip(";")
    if ";" in s:                                       return False, "multiple statements are not allowed"
    if re.search(r"--|/\*", s):                        return False, "SQL comments are not allowed"
    if not re.match(r"^select\b", s, re.I):            return False, "only SELECT is allowed"
    if FORBIDDEN.search(s):                            return False, "forbidden keyword"
    tables = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w]*)", s, re.I))
    if not tables <= ALLOWED_TABLES:                   return False, f"table(s) not allowed: {sorted(tables - ALLOWED_TABLES)}"
    return True, "ok"


def run_guarded(con: sqlite3.Connection, sql: str, max_rows: int = 5):
    ok, why = validate_sql(sql)
    if not ok:
        return f"BLOCKED ({why})"
    cur = con.execute(sql)
    rows = cur.fetchmany(max_rows + 1)                 # row cap: protects memory and the model's context window
    note = f"  [truncated to {max_rows} rows]" if len(rows) > max_rows else ""
    return str(rows[:max_rows]) + note


# a throwaway in-memory DB, opened through a function that would also use mode=ro on a real file (see LC-15)
con = sqlite3.connect(":memory:")
con.executescript("""
CREATE TABLE products(id INTEGER, name TEXT, price REAL);
CREATE TABLE orders(id INTEGER, product_id INTEGER, qty INTEGER);
CREATE TABLE users(id INTEGER, email TEXT, password_hash TEXT);
INSERT INTO products VALUES (1,'Keyboard',1500),(2,'Mouse',600);
INSERT INTO orders VALUES (1,1,2),(2,2,5);
INSERT INTO users VALUES (1,'a@b.com','$2b$hash');
""")
con.executemany("INSERT INTO orders VALUES (?,?,?)", [(i, 1, 1) for i in range(10, 20)])

attempts = [
    "SELECT name, price FROM products",
    "SELECT * FROM orders",                                          # many rows -> truncated
    "SELECT * FROM users",                                           # table outside the allowlist
    "SELECT name FROM products; DROP TABLE products",                # statement stacking
    "DELETE FROM orders",                                            # write
    "SELECT name FROM products -- ignore the rest",                  # comment trick
    "SELECT name FROM products JOIN users ON 1=1",                   # sneaking a table in via JOIN
    "SELECT * FROM sqlite_master",                                   # schema discovery
]
for sql in attempts:
    print(f"{sql[:62]:62} -> {run_guarded(con, sql)}")

print("\nLayers: (1) this validator  (2) a READ-ONLY database connection/user  (3) a DB account with grants only on")
print("these tables. Any single layer can have a bug; all three together rarely do. String checks are a")
print("teaching baseline: production systems parse the SQL (e.g. with sqlglot) instead of using regexes.")


"""
       AI AGENT GENERATES SQL
       Example: SELECT * FROM users
                    |
                    v
       +--------------------------+
       | 1. CHECK SQL STATEMENT   |
       | Is it a SELECT query?    |
       | Only one statement?      |
       | No SQL comments?         |
       +--------------------------+
                    |
             +------+------+
             |             |
          INVALID         VALID
             |             |
             v             v
          BLOCKED   +----------------------+
                    | 2. CHECK KEYWORDS    |
                    | INSERT, DELETE, DROP |
                    | UPDATE, ALTER, etc.  |
                    +----------------------+
                              |
                       +------+------+
                       |             |
                    FORBIDDEN      SAFE SO FAR
                       |             |
                       v             v
                    BLOCKED   +----------------------+
                              | 3. CHECK TABLES      |
                              | Only products/orders? |
                              +----------------------+
                                        |
                                 +------+------+
                                 |             |
                             NOT ALLOWED     ALLOWED
                                 |             |
                                 v             v
                              BLOCKED   +------------------+
                                        | 4. EXECUTE SQL   |
                                        | Fetch max 6 rows |
                                        +------------------+
                                                  |
                                                  v
                                        +------------------+
                                        | 5. RETURN MAX 5  |
                                        | Extra row means  |
                                        | results truncated|
                                        +------------------+
                                                  |
                                                  v
                                          SAFE-LIMITED
                                          QUERY RESULT
"""