from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# ---- (예시용) 상태/노드 정의 ----
class State(TypedDict):
    x: int

def node_a(state: State) -> State:
    return {"x": state["x"] + 1}

def node_b(state: State) -> State:
    return {"x": state["x"] * 2}

def node_c(state: State) -> State:
    return {"x": state["x"] - 3}

# ---- 그래프 구성 ----
builder = StateGraph(State)
builder.add_node("node_a", node_a)
builder.add_node("node_b", node_b)
builder.add_node("node_c", node_c)
builder.add_edge(START, "node_a")
builder.add_edge("node_a", "node_b")
builder.add_edge("node_b", "node_c")
builder.add_edge("node_c", END)

checkpointer = InMemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
    # static interrupt: node_a 실행 "전"에 멈추고,
    interrupt_before=["node_a"],
    # node_b, node_c 실행 "후"에 멈춤
    interrupt_after=["node_b", "node_c"],
)

# ---- 실행 & 재개 ----
config = {"configurable": {"thread_id": "some_thread"}}
inputs = {"x": 10}

# 1) 최초 실행: node_a "전"에서 멈춤
res = graph.invoke(inputs, config=config)
print(res.get("__interrupt__", []))        # 인터럽트 메타 확인

# 2) 재개: node_a 실행으로 진행
res = graph.invoke(Command(resume=True), config=config)
print(res.get("__interrupt__", []))        # node_b "후"에서 다시 멈춤

# 3) 재개: node_c로 진행
res = graph.invoke(Command(resume=True), config=config)
print(res.get("__interrupt__", []))        # node_c "후"에서 다시 멈춤

# 4) 마지막 재개: END 도달
final = graph.invoke(Command(resume=True), config=config)
print(final)                                # {'x': 최종값}
