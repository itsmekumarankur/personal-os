import asyncio
import json

import httpx

from a2a.client import A2ACardResolver
from a2a.helpers import display_agent_card

from common.a2a_helpers import ask

URL = "http://localhost:9101"


async def main():
    # --- 1. Discovery: every A2A agent publishes a card at a well-known path
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, URL).get_agent_card()
        print("=== Agent card ===")
        display_agent_card(card)

        # --- Raw JSON-RPC call (what the SDK does under the hood)
        payload = {
            "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
            "params": {"message": {"role": "ROLE_USER", "messageId": "m-1",
                                   "parts": [{"text": "raw hello"}]}},
        }
        r = await http.post(URL + "/", json=payload, headers={"A2A-Version": "1.0"})
        print("\n=== Raw JSON-RPC response ===")
        print(json.dumps(r.json(), indent=2)[:600])

    # --- 2. SDK client
    result = await ask(URL, "Hi from the SDK client")
    print("\n=== SDK client ===")
    print(result["text"])


if __name__ == "__main__":
    asyncio.run(main())


"""
This code is showing two different ways to communicate with an A2A Agent:
1. Directly using HTTP + JSON-RPC (manual way)
2. Using the SDK helper (easy way)



                 A2A CLIENT PROGRAM
                        |
                        |
                        v
              URL = localhost:9101
                        |
          ┌─────────────┴─────────────┐
          │                           │
          │  STEP 1: DISCOVERY        │
          │                           │
          ▼                           │
   ┌───────────────────┐              │
   │ A2ACardResolver   │              │
   │                   │              │
   │ "Who are you?"    │              │
   └─────────┬─────────┘              │
             │                        │
             ▼                        │
   ┌───────────────────┐              │
   │   A2A AGENT       │              │
   │   localhost:9101  │              │
   └─────────┬─────────┘              │
             │                        │
             │ Returns Agent Card     │
             ▼                        │
   ┌───────────────────┐              │
   │ 🤖 Agent Name     │              │
   │ 📝 Description    │              │
   │ 🛠️ Availabl Skills│              │
   └───────────────────┘              │
                                      │
══════════════════════════════════════╪══════
                                      │
        STEP 2: TALK TO AGENT         │
                                      │
          TWO DIFFERENT WAYS          │
                                      │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼

   METHOD 1: MANUAL                 METHOD 2: SDK
   ────────────────                 ─────────────

   Create JSON-RPC                  ask(URL, message)
   message manually                       |
          |                                |
          v                                v
   ┌───────────────┐                ┌───────────────┐
   │ {             │                │ SDK handles   │
   │  method:      │                │ the complex   │
   │ "SendMessage" │                │ communication │
   │  message:     │                └───────┬───────┘
   │ "raw hello"   │                        |
   │ }             │                        |
   └───────┬───────┘                        |
           |                                |
           v                                v
      HTTP POST                         Send Message
           |                                |
           └───────────────┬────────────────┘
                           |
                           v
                  ┌────────────────┐
                  │   A2A AGENT    │
                  │                │
                  │ Process Message│
                  └────────┬───────┘
                           |
                           v
                  ┌────────────────┐
                  │    RESPONSE    │
                  │                │
                  │ "Hello..."     │
                  └────────────────┘
"""