# Import relevant functionality
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent

import os
import getpass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the variables
api_key = os.getenv("ANTHROPIC_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
os.environ["TAVILY_API_KEY"] = tavily_api_key

if not api_key:
  api_key = getpass.getpass("Enter API key for Anthropic: ")

model = init_chat_model("claude-3-7-sonnet-20250219", model_provider="anthropic")

search = TavilySearch(max_results=2)
# search_results = search.invoke("What is the weather in SF")
# print(search_results)
# If we want, we can create other tools.
# Once we have all the tools we want, we can put them in a list that we will reference later.
tools = [search]

model_with_tools = model.bind_tools(tools)

memory = MemorySaver()

agent_executor = create_react_agent(model, tools, checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}

var = 1
while var:
    query = input("Enter a query: ")
    if query == "exit":
        var = 0
    else:
        for step in agent_executor.stream(
            {"messages": [("user", query)]}, config, stream_mode="values"
        ):
            step["messages"][-1].pretty_print()

print('--------------------------------')

# If we want, we can create other tools.
# Once we have all the tools we want, we can put them in a list that we will reference later.

# query = "Hi!"
# response = model.invoke([{"role": "user", "content": query}])
# response.text()