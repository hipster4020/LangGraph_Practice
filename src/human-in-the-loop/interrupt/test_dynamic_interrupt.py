from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

# 1) State 타입 정의
class State(TypedDict):
    some_text: str

# 2) 사람 입력을 기다리는 노드
def human_node(state: State) -> State:
    value = interrupt({"text_to_revise": state["some_text"]})
    return {"some_text": value}

# 3) 그래프 구성
graph_builder = StateGraph(State)
graph_builder.add_node("human_node", human_node)
graph_builder.add_edge(START, "human_node")
checkpointer = InMemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)

# 4) 실행 → 인터럽트 발생
config = {"configurable": {"thread_id": "some_id"}}
result = graph.invoke({"some_text": "original text"}, config=config)
print(result.get("__interrupt__", None))
#  -> Interrupt 객체 정보 출력됨

# 5) 인터럽트 재개
resumed = graph.invoke(Command(resume="Edited text"), config=config)
print(resumed)
#  -> {"some_text": "Edited text"}
