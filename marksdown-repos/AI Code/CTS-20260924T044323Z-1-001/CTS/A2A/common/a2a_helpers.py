"""Helpers for creating and serving small A2A agents."""

from uuid import uuid4

import uvicorn
from a2a.client import ClientConfig, create_client
from starlette.applications import Starlette
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Message,
    Part,
    Role,
    SendMessageRequest,
)


def make_card(
    name: str,
    description: str,
    port: int,
    skills: list[AgentSkill],
    streaming: bool = False,
) -> AgentCard:
    """Build an agent card for a local A2A server."""
    return AgentCard(
        name=name,
        description=description,
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(
                url=f"http://localhost:{port}/",
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(streaming=streaming),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=skills,
    )


def build_app(executor: AgentExecutor, card: AgentCard):
    """Build a Starlette application for an A2A executor and card."""
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = [
        *create_agent_card_routes(card),
        *create_jsonrpc_routes(request_handler, rpc_url="/"),
        *create_rest_routes(request_handler),
    ]
    return Starlette(
        routes=routes,
    )


def serve(app, port: int) -> None:
    """Serve an A2A application on localhost."""
    uvicorn.run(app, host="0.0.0.0", port=port)


async def ask(url: str, text: str) -> dict[str, str]:
    """Send one text message to an A2A agent and return its text response."""
    client = await create_client(url, ClientConfig(streaming=False))
    request = SendMessageRequest(
        message=Message(
            message_id=str(uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=text)],
        )
    )

    response_text = ""
    async for response in client.send_message(request):
        if response.HasField("message"):
            response_text = "".join(
                part.text for part in response.message.parts if part.HasField("text")
            )

    await client.close()
    return {"text": response_text}