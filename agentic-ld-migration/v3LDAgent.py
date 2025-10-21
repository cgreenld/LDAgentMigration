import os
import json
from typing import Any, Dict, List

from dotenv import load_dotenv

# LangGraph / LangChain
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model

# LaunchDarkly
import ldclient
from ldclient.context import Context
from ldclient.config import Config
from ldai.client import LDAIClient, LDAIAgentConfig, LDAIAgentDefaults
import json
from typing import Any, Dict, List, Optional

load_dotenv()

# --- LaunchDarkly: initialize LD + AI client and build a Context for progressive rollout ---
ldclient.set_config(Config(os.getenv("LD_SDK_KEY", "")))
aiclient = LDAIClient(ldclient.get())
aiKeys = os.getenv("AI_KEYS", "").split(",")

# You control progressive rollout & targeting with these attributes in LD
ld_context = Context.builder("agent-session-123") \
    .kind("request") \
    .set("env", os.getenv("APP_ENV", "dev")) \
    .set("team", os.getenv("TEAM", "platform")) \
    .set("tenant", os.getenv("TENANT", "acme-inc")) \
    .set("request_id", "1234567890") \
    .set("use_case", "agentic-account-migration") \
    .set("request_type", "account-migration") \
    .set("request_status", "pending") \
    .set("request_created_at", "2025-01-01") \
    .set("request_updated_at", "2025-01-01") \
    .build()

fallback = {"enabled": False}  # safe default when disabled or missing config

agents = aiclient.agents([
    LDAIAgentConfig(
        key=aiKeys[0],
        default_value=LDAIAgentDefaults(
            enabled=False,
            instructions=""
        ),
        variables={}
    ),
    # LDAIAgentConfig(
    #     key='writing_agent',
    #     default_value=LDAIAgentDefaults(
    #         enabled=True,
    #         instructions='You are a writing assistant.'
    #     ),
    #     variables={'style': 'academic'}
    # )
], ld_context)

agent_cfg = agents[aiKeys[0]];

if not agent_cfg.enabled:
    print("Agent disabled by LaunchDarkly; exiting.")
    raise SystemExit(0)

if agent_cfg.enabled:
    # Typed access
    model = agent_cfg.model
    provider = agent_cfg.provider
    instructions = agent_cfg.instructions
    max_token = model.get_parameter("max_tokens") if model else None
    tools = model.get_parameter("tools") if model else None
    require_approval = model.get_custom("require_approval") if model else None
    dry_run = model.get_custom("dry_run") if model else None
    provider = provider.name if provider else None
    max_results = model.get_parameter("tavily_max_results") if model else None

    # Metrics
    if agent_cfg.tracker:
        agent_cfg.tracker.track_success()
else:
    if agent_cfg.tracker:
        agent_cfg.tracker.track_failure("disabled")


# --- Build tools based on allowlist (dynamic) ---
tools = []
if "search" in tools:
    tools.append(TavilySearch(max_results=max_results))

# --- Build model dynamically from LD config ---
model = init_chat_model(model.name, model_provider=provider)

# --- Wrap into a ReAct agent with memory ---
memory = MemorySaver()
agent_executor = create_react_agent(model, tools, checkpointer=memory)
config = {"configurable": {"thread_id": "default-thread"}}

# --- Optional approval gate driven by LD config ---
def approval_gate(plan_summary: str) -> bool:
    if not require_approval:
        return True
    print("\n" + "="*50)
    print("PLAN APPROVAL REQUIRED (LD controlled)")
    print("="*50)
    print(plan_summary)
    print("="*50)
    while True:
        resp = input("Approve? (y/n): ").strip().lower()
        if resp in ("y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")

# --- Example “dynamic plan then execute” loop using the agent ---
def summarize_plan(messages: List[Dict[str, str]]) -> str:
    # Trivial summarizer; in practice, ask the model to summarize proposed steps
    return f"About to run with tools={tools}, dry_run={dry_run}"

def execute(query: str) -> None:
    # Step 1: let the agent think (and read tools only)
    plan_msgs = [{"role": "user", "content": f"Plan steps for: {query}. Only plan, do not execute yet."}]
    for step in agent_executor.stream({"messages": plan_msgs}, config, stream_mode="values"):
        pass  # stream planning tokens if desired

    plan_summary = summarize_plan(plan_msgs)

    # Step 2: approval (if required)
    if not approval_gate(plan_summary):
        print("Plan rejected.")
        return

    # Step 3: execute (respect DRY_RUN)
    if dry_run:
        print("[DRY RUN] Skipping execution; plan only.")
        return

    exec_msgs = [{"role": "user", "content": f"Execute: {query}. Perform the necessary steps."}]
    for step in agent_executor.stream({"messages": exec_msgs}, config, stream_mode="values"):
        step["messages"][-1].pretty_print()

if __name__ == "__main__":
    print("LD agent config loaded. Dynamic controls active.")
    print(f"- model={model}, tools={tools}, approval={require_approval}, dry_run={dry_run}")
    while True:
        q = input("\nEnter a query (or 'exit'): ").strip()
        if q.lower() == "exit":
            break
        execute(q)