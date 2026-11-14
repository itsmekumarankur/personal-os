# a2a_framework.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@dataclass
class AgentSkill:
    id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

@dataclass
class AgentCard:
    name: str
    description: str
    port: int
    skills: List[AgentSkill]
    streaming: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "port": self.port,
            "streaming": self.streaming,
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "tags": s.tags,
                    "examples": s.examples
                } for s in self.skills
            ]
        }

def make_card(name: str, description: str, port: int, skills: List[AgentSkill], streaming: bool = False) -> AgentCard:
    return AgentCard(name=name, description=description, port=port, skills=skills, streaming=streaming)

def build_app(executor_handler: Callable, card: AgentCard) -> FastAPI:
    app = FastAPI(title=card.name, description=card.description)

    # 1. Discovery Endpoint
    @app.get("/.well-known/agent.json")
    async def get_agent_card():
        return card.to_dict()

    # 2. Skill Execution Endpoint
    @app.post("/a2a/execute")
    async def execute_skill(request: Request):
        body = await request.json()
        skill_id = body.get("skill_id")
        params = body.get("params", {})
        
        result = await executor_handler(skill_id, params)
        return {"status": "success", "skill_id": skill_id, "output": result}

    return app



"""
                    A2A FRAMEWORK
          "How other agents discover and use me"
════════════════════════════════════════════════════

                    ┌─────────────────┐
                    │   Agent Skills  │
                    │─────────────────│
                    │ 🆔 id           │
                    │ 📛 name         │
                    │ 📝 description  │
                    │ 🏷️ tags         │
                    │ 💡 examples     │
                    └────────┬────────┘
                             │
                             │ Skills describe
                             ▼
                    ┌─────────────────┐
                    │   AGENT CARD    │
                    │─────────────────│
                    │ 🤖 Agent Name   │
                    │ 📝 Description  │
                    │ 🚪 Port         │
                    │ 📋 Skills       │
                    │ 🌊 Streaming?   │
                    └────────┬────────┘
                             │
                             │ Agent Card is given to
                             ▼
              ┌──────────────────────────┐
              │      build_app()         │
              │                          │
              │ Creates a FastAPI Agent  │
              └────────────┬─────────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼

┌────────────────────────┐    ┌────────────────────────┐
│  1️⃣ DISCOVERY          │    │  2️⃣ EXECUTION          │
│                        │    │                        │
│ GET                    │    │ POST                   │
│ /.well-known/agent.json│    │ /a2a/execute           │
│                        │    │                        │
│ "WHO ARE YOU?"         │    │ "DO THIS SKILL!"       │
└───────────┬────────────┘    └───────────┬────────────┘
            │                             │
            ▼                             ▼
      Returns Agent Card            Receives Request
                                        │
                                        ▼
                                  ┌──────────────┐
                                  │  skill_id    │
                                  │  + params    │
                                  └──────┬───────┘
                                         │
                                         ▼
                               ┌─────────────────────┐
                               │ executor_handler()  │
                               │                     │
                               │ Executes the skill  │
                               └──────────┬──────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │   SUCCESS RESPONSE  │
                               │─────────────────────│
                               │ status: success     │
                               │ skill_id: ...       │
                               │ output: result      │
                               └─────────────────────┘
"""