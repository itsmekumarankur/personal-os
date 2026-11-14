"""Settings from environment variables, checked at start-up. A bad setting stops the service
immediately with a clear message, instead of failing on the first request."""
import hmac
import json
import os
from dataclasses import dataclass, field

ROLES = {"customer", "approver", "ops"}


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Principal:
    """Who is calling. Built from the API key, never from anything the caller or the model writes."""
    id: str
    role: str
    account_id: str | None = None


@dataclass(frozen=True)
class Settings:
    api_keys: dict = field(default_factory=dict)         # {key: Principal}
    model: str = "claude-sonnet-4-5"
    db_path: str = "./data/platform.db"
    rate_limit_per_min: int = 30
    daily_token_budget: int = 200_000                   # per customer, per UTC day
    max_refund: float = 5000.0
    max_turns: int = 6
    input_guard: str = "block"                          # "block" or "log"
    log_level: str = "INFO"
    enable_docs: bool = False                           # /docs lists every endpoint: off by default

    def authenticate(self, token: str) -> Principal | None:
        """Constant-time comparison against every key, so timing does not reveal which part matched."""
        found = None
        for key, principal in self.api_keys.items():
            if hmac.compare_digest(token.encode(), key.encode()):
                found = principal
        return found

    def principal_by_id(self, principal_id: str) -> Principal | None:
        return next((p for p in self.api_keys.values() if p.id == principal_id), None)


def parse_api_keys(raw: str) -> dict:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f"API_KEYS_JSON is not valid JSON: {e}") from e
    if not isinstance(data, dict) or not data:
        raise ConfigError('API_KEYS_JSON must be a non-empty JSON object: {"<key>": {"id": ..., "role": ...}}')
    keys, ids = {}, set()
    for key, info in data.items():
        if not isinstance(key, str) or len(key) < 16:
            raise ConfigError("every API key must be at least 16 characters")
        if not isinstance(info, dict) or info.get("role") not in ROLES or not info.get("id"):
            raise ConfigError(f"each key needs an id and a role in {sorted(ROLES)}")
        if info["role"] == "customer" and not info.get("account_id"):
            raise ConfigError(f"customer {info['id']!r} needs an account_id")
        if info["id"] in ids:
            raise ConfigError(f"duplicate id {info['id']!r}")
        ids.add(info["id"])
        keys[key] = Principal(id=info["id"], role=info["role"], account_id=info.get("account_id"))
    return keys


def load_settings(env: dict | None = None) -> Settings:
    env = os.environ if env is None else env
    if "API_KEYS_JSON" not in env:
        raise ConfigError("API_KEYS_JSON is not set")
    guard = env.get("INPUT_GUARD", "block")
    if guard not in ("block", "log"):
        raise ConfigError("INPUT_GUARD must be 'block' or 'log'")
    try:
        return Settings(
            api_keys=parse_api_keys(env["API_KEYS_JSON"]),
            model=env.get("MODEL", "claude-sonnet-4-5"),
            db_path=env.get("DB_PATH", "./data/platform.db"),
            rate_limit_per_min=int(env.get("RATE_LIMIT_PER_MIN", "30")),
            daily_token_budget=int(env.get("DAILY_TOKEN_BUDGET", "200000")),
            max_refund=float(env.get("MAX_REFUND", "5000")),
            max_turns=int(env.get("MAX_TURNS", "6")),
            input_guard=guard,
            log_level=env.get("LOG_LEVEL", "INFO").upper(),
            enable_docs=env.get("ENABLE_DOCS", "0") == "1",
        )
    except ValueError as e:
        raise ConfigError(f"a numeric setting is not a number: {e}") from e
