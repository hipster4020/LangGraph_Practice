import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain.schema import HumanMessage
from typing import List
from nodes import generate


def build_workflow(
    llm,
    store,
    namespace: tuple,
    now_time: str,
):
    app = StateGraph(dict)
    print(f"bw now_time : {now_time}")
    app.add_node("generate", generate(llm, store, namespace, now_time))
    # app.add_node("optimize", optimize(default_window))
    # app.add_node("generate", generate(llm, store, namespace, now_time))

    app.add_edge(START, "generate")
    app.add_edge("generate", END)
    # app.add_edge("agent", "optimize")
    # app.add_edge("optimize", "generate")
    # app.add_edge("generate", END)

    return app


def run_query(app, thread_id: str, question: str):
    inputs = {"messages": [HumanMessage(content=question)]}
    config = {"configurable": {"thread_id": thread_id}}
    for output in app.stream(inputs, config=config):
        answer_parts = []
        for node, part in output.items():
            for m in part.get("messages", []):
                if hasattr(m, "content"):
                    answer_parts.append(m.content)
        answer = "\n".join(answer_parts).strip()
        print(f"[{thread_id}] answer: {answer}")
    return answer


def save_graph_image(app, out_path: str = "workflow.png"):
    try:
        png = app.get_graph().draw_mermaid_png()
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(png)
        print(f"Graph saved to {out_path}")
    except Exception as e:
        print(f"[WARN] graph rendering failed: {e}")
