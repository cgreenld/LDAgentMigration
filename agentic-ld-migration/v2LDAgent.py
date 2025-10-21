# pip install langgraph langchain anthropic
from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

llm_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = llm_api_key

class State(TypedDict):
    instruction: str
    plan: Dict[str, Any] | None
    approved: bool
    results: List[Dict[str, Any]]

llm = ChatOpenAI(model="gpt-4")

def plan_node(state: State) -> State:
    # Use LLM + READ tools to compute a plan (no writes)
    # (You can call ld.list_flags here via LC Runnable/tool calling.)
    plan = {
        "projectKey": "webapp",
        "creates": [{"key": f"f{i}"} for i in range(1,6)]
    }
    return {**state, "plan": plan}

def wait_for_approval(state: State) -> State:
    # This node shows the plan to the user and collects approval.
    print("\n" + "="*50)
    print("📋 PLAN APPROVAL REQUIRED")
    print("="*50)
    print(f"Project: {state['plan']['projectKey']}")
    print(f"Features to create: {len(state['plan']['creates'])}")
    for i, item in enumerate(state['plan']['creates'], 1):
        print(f"  {i}. {item['key']}")
    print("="*50)
    
    while True:
        response = input("\nDo you approve this plan? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print("✅ Plan approved! Proceeding with execution...")
            return {**state, "approved": True}
        elif response in ['n', 'no']:
            print("❌ Plan rejected! Stopping execution.")
            return {**state, "approved": False}
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def execute_node(state: State) -> State:
    print("\n🚀 EXECUTING PLAN...")
    print("="*50)
    results = []
    for i, item in enumerate(state["plan"]["creates"], 1):
        print(f"Creating feature {i}/{len(state['plan']['creates'])}: {item['key']}")
        # call WRITE tool here (ld.create_flag)
        results.append({"key": item["key"], "status": "created"})
        print(f"  ✅ {item['key']} created successfully")
    print("="*50)
    print("🎉 All features created successfully!")
    return {**state, "results": results}

def report_node(state: State) -> State:
    # Convert results to a user-facing summary
    print("\n📊 EXECUTION SUMMARY")
    print("="*50)
    print(f"Project: {state['plan']['projectKey']}")
    print(f"Total features created: {len(state['results'])}")
    print("\nResults:")
    for result in state['results']:
        print(f"  • {result['key']}: {result['status']}")
    print("="*50)
    return state

graph = StateGraph(State)
graph.add_node("plan", plan_node)
graph.add_node("wait", wait_for_approval)
graph.add_node("execute", execute_node)
graph.add_node("report", report_node)

graph.add_edge(START, "plan")
graph.add_edge("plan", "wait")
# conditional: proceed only if approved
def approved_guard(state: State):
    return "execute" if state.get("approved") else "__end__"
graph.add_conditional_edges("wait", approved_guard, {"execute": "execute", "__end__": END})
graph.add_edge("execute", "report")
graph.add_edge("report", END)

app = graph.compile()

# --- Run the complete workflow ---
print("🎯 Starting DevCycle Feature Creation Workflow")
print("="*50)

# The graph will handle the approval flow automatically
final_state = app.invoke({
    "instruction": "Create f1..f5 in webapp", 
    "plan": None, 
    "approved": False, 
    "results": []
})

print(f"\n🏁 Workflow completed!")
print(f"Final state: {final_state}")