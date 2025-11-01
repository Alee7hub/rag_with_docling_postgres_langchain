from unittest import result
from tools import retrieve_context
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()


model = init_chat_model("gpt-5-mini")
tools = [retrieve_context]

prompt = (
    "You have access to a tool that retrieves context from multiple financial documents and reports."
    "Use the tool to help answer user queries. If so, please mention the source of the information at the end of your response."
)

agent = create_agent(
    model,
    tools,
    system_prompt=prompt
)

def run_agent(query: str):
    result = agent.invoke({
        "messages": [{"role": "user", "content": query}],
    })

    agent_response = result['messages'][-1].content

    return agent_response