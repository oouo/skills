"""Small static fixture with an agent loop, tools, state, and failures."""

import asyncio
import os as runtime_os
from dataclasses import dataclass, field
from typing import Awaitable, Callable


Tool = Callable[[str], Awaitable[str]]
TOOLS: dict[str, Tool] = {}
MODEL_NAME = runtime_os.getenv("MODEL_NAME", "fixture-model")
MAX_ROUNDS = 3


def tool(name: str):
    def register(function: Tool) -> Tool:
        TOOLS[name] = function
        return function

    return register


@tool("lookup")
async def lookup_tool(query: str) -> str:
    if not query:
        raise ValueError("query is required")
    return f"result:{query}"


@dataclass
class AgentState:
    messages: list[str] = field(default_factory=list)
    rounds: int = 0
    final_output: str | None = None


class FakeProvider:
    async def complete(self, messages: list[str], model: str) -> dict[str, str]:
        if any(message.startswith("tool:") for message in messages):
            return {"final": "done"}
        return {"tool": "lookup", "arguments": messages[-1]}


async def dispatch_tool(name: str, arguments: str) -> str:
    selected = TOOLS.get(name)
    if selected is None:
        raise KeyError(f"unknown tool: {name}")
    return await selected(arguments)


async def run_agent(user_input: str, provider: FakeProvider) -> AgentState:
    state = AgentState(messages=[user_input])
    while state.rounds < MAX_ROUNDS:
        state.rounds += 1
        response = await provider.complete(state.messages, MODEL_NAME)
        if "final" in response:
            state.final_output = response["final"]
            return state
        result = await dispatch_tool(response["tool"], response["arguments"])
        state.messages.append(f"tool:{result}")
    raise RuntimeError("agent reached its maximum rounds")


def main() -> int:
    mode = runtime_os.environ["AGENT_MODE"]
    state = asyncio.run(run_agent(mode, FakeProvider()))
    print(state.final_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
