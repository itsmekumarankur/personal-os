from a2a.helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentSkill

from common.a2a_helpers import build_app, make_card, serve


PORT = 9101

class HelloExecutor(AgentExecutor):
    """Message only pattern : enqueue exactly one message and return a response with the same message."""

    async def execute(self, context : RequestContext, event_queue : EventQueue) -> None:
        user_text = context.get_user_input()
        reply = f"Hello, User said '{user_text}'!. I am an A2A Agent running on port {PORT}."
        await event_queue.enqueue_event(new_text_message(reply, context_id=context.context_id))

    async def cancel(self, context : RequestContext, event_queue : EventQueue) -> None:
        raise NotImplementedError("Cancel is not implemented for HelloExecutor.")


skill = AgentSkill(id = "greet", name = "Greet", description = "Greets the caller and echos their text",
                   tags = ["hello", "echo"], examples = ["hi there"])

card = make_card("Hello Agent", "Minimal A2A agent that greets you", PORT, [skill], streaming = False)

app = build_app(HelloExecutor(), card)


if __name__ == "__main__" :
    serve(app, PORT)