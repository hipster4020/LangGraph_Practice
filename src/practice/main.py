import time
import hashlib
from hydra import compose, initialize
from workflow import build_workflow, run_query, save_graph_image
from langchain_openai import ChatOpenAI
from langgraph.store.sqlite import SqliteStore
from langgraph.checkpoint.sqlite import SqliteSaver


def main():
    with initialize(version_base="1.2", config_path="../../../config/"):
        cfg = compose(config_name="config")

    llm = ChatOpenAI(**cfg.OPENAI)
    now_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    print(f"now_time : {now_time}")

    # # ✅ store는 context manager로 쓰지 말고 그냥 생성
    # store = SqliteStore.from_conn_string(cfg.PATH.memory_db)
    
    # ✅ 2. thread_id / namespace 구성
    questions = "내 이름은 patrick이야"
    # questions = "내가 앞서서 뭐라고 물어봤지?"
    thread_id = "thread_id_1"
    user_id = "patrick.park"
    safe_user_id = hashlib.sha256(user_id.encode()).hexdigest()
    namespace = ("memory", safe_user_id, "threads", thread_id)

    # # ✅ 3. 저장된 state 확인
    # with SqliteStore.from_conn_string(cfg.PATH.memory_db) as store:
    #     value = store.get(namespace, "state")
    #     print(f"value : {value}")
    # store는 일반 인스턴스 생성
    store = SqliteStore.from_conn_string(cfg.PATH.memory_db)
    # 이전 state 출력
    value = store.get(namespace, "state")
    print(f"value : {value}")

    with SqliteSaver.from_conn_string(cfg.PATH.memory_db) as checkpointer:
        workflow = build_workflow(llm, store, namespace, now_time)
        app = workflow.compile(checkpointer=checkpointer, store=store)
        answer = run_query(app, thread_id, questions)
        print(answer)
        save_graph_image(app, cfg.PATH.graph_output)



    # # ✅ 4. SQLite Checkpointer로 상태 관리
    # with SqliteSaver.from_conn_string(cfg.PATH.memory_db) as checkpointer:
    #     workflow = build_workflow(
    #         llm,
    #         store,
    #         namespace,
    #         now_time,
    #     )
    #     # ✅ Store + Checkpointer 모두 연결
    #     app = workflow.compile(checkpointer=checkpointer, store=store)

    #     # ✅ 5. 같은 thread_id로 config 전달
    #     # config = {"configurable": {"thread_id": thread_id}}
    #     answer = run_query(app, thread_id, questions)
    #     print(answer)

    #     save_graph_image(app, cfg.PATH.graph_output)

if __name__ == "__main__":
    main()
