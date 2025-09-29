from typing import Any, Dict, Annotated, TypedDict
import prompt as pt
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# State 정의
class State(TypedDict):
    # 메시지 정의(list type 이며 add_messages 함수를 사용하여 메시지를 추가)
    messages: Annotated[list[BaseMessage], add_messages]
    window_size: int  # 유지할 메시지 수


# Nodes
def generate(llm, store, namespace: tuple, now_time: str):
    def generate_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        현재 상태를 기반으로 에이전트 모델을 호출하여 응답을 생성합니다.
        질문에 따라 검색 도구를 사용하여 검색을 결정하거나 단순히 종료합니다.

        Args:
            state (messages): 현재 상태

        Returns:
            dict: 메시지에 에이전트 응답이 추가된 업데이트된 상태
        """
        # 노드 간 걸린 시간
        print("generate start...!")

        if store:
            item = store.get(namespace=namespace, key=namespace[1])
            print(f"item : {item}")

            retrieved = None
            # item이 None이 아닌 경우, 실제 stored value 꺼내기
            if item is not None:
                # 예: item.value 또는 item.data 속성
                # 정확한 속성명은 Item 클래스 정의 참고
                retrieved = item.value if hasattr(item, "value") else None
            print(f"retrieved : {retrieved}")

            if retrieved and "summary" in retrieved:
                system = SystemMessage(
                    content = f"Today is {now_time}.\n" +
                        f"이전 요약 기억: {retrieved['summary']}\n\n" +
                        f"역할 : {pt.system_msg}\n다음 질문에 답하세요.\n"
                )
            else:
                system = SystemMessage(
                    content = f"Today is {now_time}.\n" + pt.system_msg
                )
        else:
            system = SystemMessage(
                content = f"Today is {now_time}.\n" + pt.system_msg
            )

        msgs = state["messages"]
        prompt = [system] + msgs
        print(f"prompt : {prompt}")
        response = llm.invoke(prompt)
        messages = msgs + [response]

        texts = [m.content for m in messages if hasattr(m, "content")]
        new_summary = "\n".join(texts[-5:])

        if store:
            store.put(
                namespace=namespace,
                key=namespace[1],
                value = {"summary": new_summary},
            )

        return {"messages": [response]}
    return generate_fn


# def optimize(default_window: int):
#     def optimize_fn(state: Dict[str, Any]) -> Dict[str, Any]:
#         msgs = state.get("messages", [])
#         size = state.get("window_size", default_window)
#         if len(msgs) > size:
#             state["messages"] = msgs[-size:]
#         return state
#     return optimize_fn

# def generate(llm, store, namespace: tuple, now_time: str):
#     def generate_fn(state: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         LLM을 사용하여 현재 메시지 히스토리를 바탕으로 응답을 생성하는 노드 팩토리 함수입니다.
#         system_prompt: 응답 생성 시 앞에 포함할 시스템 프롬프트 (선택)
#         """
#         # state["messages"] 에는 이전 대화 메시지들이 저장되어 있어야 함
#         msgs = state.get("messages", [])
#         # 새 응답을 위해 LLM 호출
#         # 메시지 프롬프트 구성
#         if store:
#             retrieved = store.get(namespace=namespace, key=namespace[1])
#             # 예: retrieved = {"summary": "..."} 등
#             if retrieved and "summary" in retrieved:
#                 # summary 정보를 시스템 메시지나 프롬프트로 주입
#                 system = SystemMessage(
#                     content=f"Today is {now_time}.\n" + f"이전 요약 기억: {retrieved['summary']}\n\n역할 : {pt.gen_prompt}\n다음 질문에 답하세요.\n"
#                 )
#             else:
#                 system = SystemMessage(
#                     content=f"Today is {now_time}.\n" + pt.gen_prompt
#                 )
#         else:
#             system = SystemMessage(
#                 content=f"Today is {now_time}.\n" + pt.gen_prompt
#             )
        
#         # 기존 메시지 + system 메시지
#         msgs = state["messages"]
#         prompt = [system] + msgs
#         print(f"prompt : {prompt}")
#         response = llm.invoke(prompt)
#         messages = msgs + [response]
#         # 응답을 받은 다음, 요약 알고리즘 등을 써서 새 요약 생성
#         texts = [m.content for m in messages if hasattr(m, "content")]
#         new_summary = "\n".join(texts[-5:])  # 최근 5개만 포함
        
#         # 장기 기억 저장소에 저장
#         if store:
#             store.put(
#                 namespace=namespace,
#                 key=namespace[1],
#                 value={"summary": new_summary},
#             )
        
#         prompt_msgs = []
#         prompt_msgs.append(SystemMessage(content=pt.gen_prompt))
#         prompt_msgs.extend(msgs)
#         print(f"prompt_msgs : {prompt_msgs}")
#         # LLM 호출
#         response = llm.invoke(prompt_msgs)
#         # 응답 메시지를 state 업데이트로 반환
#         return {"messages": [response]}
#     return generate_fn
