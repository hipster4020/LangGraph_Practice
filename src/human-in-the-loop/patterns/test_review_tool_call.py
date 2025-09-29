from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

# ---- 상태 정의 ----
class EmailState(TypedDict):
    recipient: str
    subject: str
    body: str
    action: Literal["approve", "edit", "feedback"] | None
    updated_body: str | None

# ---- 노드 정의 ----
def email_planner_node(state: EmailState) -> EmailState:
    # LLM 역할로 이메일 내용을 작성했다고 가정
    return {
        **state,
        "recipient": "john@example.com",
        "subject": "Meeting Reminder",
        "body": "Don’t forget our meeting tomorrow at 2 PM.",
        "action": None,
        "updated_body": None,
    }

def human_review_tool_call(state: EmailState) -> Command:
    # 사람이 검토할 내용과 질문사항 전달
    review = interrupt({
        "question": "Review this email before sending",
        "email": {
            "to": state["recipient"],
            "subject": state["subject"],
            "body": state["body"],
        }
    })
    action = review.get("action")
    data = review.get("data")

    # 사람 선택에 따라 다른 경로로 진행
    if action == "approve":
        return Command(goto="send_email", update={"action": "approve"})
    if action == "edit":
        return Command(
            goto="send_email",
            update={"action": "edit", "updated_body": data.get("body", state["body"])},
        )
    if action == "feedback":
        return Command(goto="end", update={"action": "feedback"})
    raise ValueError("Invalid review action")

def send_email_node(state: EmailState) -> EmailState:
    if state["action"] == "approve":
        final_body = state["body"]
    elif state["action"] == "edit" and state["updated_body"]:
        final_body = state["updated_body"]
    else:
        final_body = state["body"]  # fallback
    # 실제 이메일 발송 로직을 여기에 넣을 수 있습니다.
    print(f"Sending email to {state['recipient']}")
    print(f"Subject: {state['subject']}")
    print(f"Body: {final_body}")
    return {**state, "body": final_body}

# ---- 그래프 구성 ----
builder = StateGraph(EmailState)
builder.add_node("plan", email_planner_node)
builder.add_node("review", human_review_tool_call)
builder.add_node("send_email", send_email_node)
builder.add_edge(START, "plan")
builder.add_edge("plan", "review")
builder.add_edge("review", "send_email")
builder.add_edge("send_email", END)

graph = builder.compile(checkpointer=InMemorySaver())

# ---- 실행 흐름 ----
config = {"configurable": {"thread_id": "thread1"}}
initial = {"recipient": "", "subject": "", "body": "", "action": None, "updated_body": None}

# (1) 실행 → 인간 검토 포인트에서 중단
res = graph.invoke(initial, config=config)
print(res.get("__interrupt__", []))

# (2) 사람의 응답 (예: approve/edit/feedback 선택)
# 예: 수정 요청 시
resume_payload = {"action": "edit", "data": {"body": "Updated meeting time: 3 PM."}}
res2 = graph.invoke(Command(resume=resume_payload), config=config)

# (3) 이메일 전송까지 이어 실행
res3 = graph.invoke(Command(resume=True), config=config)
print("Final State:", res3)
