# server_agent.py
import uvicorn
from a2a_framework import AgentSkill, make_card, build_app

PORT = 8000

# 1. Implement Execution Handler
class HelloExecutor:
    async def __call__(self, skill_id: str, params: dict) -> dict:
        if skill_id == "greet":
            user_text = params.get("text", "world")
            return {
                "message": f"Hello! You said: '{user_text}'",
                "echo": user_text
            }
        return {"error": f"Unknown skill: {skill_id}"}

# 2. Define Skill Metadata
skill = AgentSkill(
    id="greet",
    name="Greet",
    description="Greets the caller and echoes their text.",
    tags=["hello", "echo"],
    examples=["hi there"]
)

# 3. Create Agent Card
card = make_card(
    name="Hello Agent",
    description="Minimal A2A agent that greets you.",
    port=PORT,
    skills=[skill],
    streaming=False
)

# 4. Build App Assembly
app = build_app(HelloExecutor(), card)

if __name__ == "__main__":
    print(f"🚀 Starting A2A Agent on http://localhost:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

