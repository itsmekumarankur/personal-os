# client_agent.py
import asyncio
import httpx

AGENT_BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient() as client:
        # Step 1: Discover Agent Capabilities (Fetch Agent Card)
        print("🔍 [Client Agent] Querying target agent card...")
        card_response = await client.get(f"{AGENT_BASE_URL}/.well-known/agent.json")
        card = card_response.json()
        
        print(f"✅ Discovered Agent: {card['name']}")
        print(f"📋 Available Skills: {[s['id'] for s in card['skills']]}\n")

        # Step 2: Programmatically Execute the 'greet' Skill
        print("📤 [Client Agent] Sending task execution request...")
        payload = {
            "skill_id": "greet",
            "params": {"text": "Architecting multi-agent systems"}
        }
        
        exec_response = await client.post(f"{AGENT_BASE_URL}/a2a/execute", json=payload)
        res_data = exec_response.json()
        
        print("📥 [Client Agent] Received Output:")
        print(res_data)

if __name__ == "__main__":
    asyncio.run(main())