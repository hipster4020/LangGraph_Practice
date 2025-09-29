from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from hydra import compose, initialize
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# State
class InputState(TypedDict):
    user_input: str
class OutputState(TypedDict):
    graph_output: str
class OverallState(TypedDict):
    foo: str
class PrivateState(TypedDict):
    bar: str

# Nodes
def node1(state: InputState) -> OverallState:
    # Write to OverallState
    return {"foo": state["user_input"] + " name"}
def node2(state: OverallState) -> PrivateState:
    # Read from OverallState, write to PrivateState
    return {"bar": state["foo"] + " is"}
def node3(state: PrivateState) -> OutputState:
    # Read from PrivateState, write to OutputState
    return {"graph_output": state["bar"] + " Lance"}

# StateGraph
builder = StateGraph(
    OverallState,
    input_schema=InputState,
    output_schema=OutputState,
)
builder.add_node("node1", node1)
builder.add_node("node2", node2)
builder.add_node("node3", node3)
builder.add_edge(START, "node1")
builder.add_edge("node1", "node2")
builder.add_edge("node2", "node3")
builder.add_edge("node3", END)


checkpointer = InMemorySaver()
long_term_store = InMemoryStore()
graph = builder.compile(checkpointer=checkpointer, store=long_term_store)

# Invoke the graph
user_id = "1"
config = {"configurable": {"thread_id": "1", "user_id": user_id}}

# First let's just say hi to the AI
for update in graph.stream(
    {
        "user_input": "My"
    }, 
    config=config, 
    stream_mode="updates",
):
    print(update)