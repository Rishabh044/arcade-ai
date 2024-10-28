import os
from datetime import datetime

from configuration import AgentConfigurable
from langchain_arcade import ArcadeToolManager
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

# Initialize the Arcade Tool Manager with your API key
arcade_api_key = os.getenv("ARCADE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

toolkit = ArcadeToolManager(api_key=arcade_api_key)
# Retrieve tools compatible with LangGraph
tools = toolkit.get_tools(langgraph=True)
tool_node = ToolNode(tools)

PROMPT_TEMPLATE = f"""
You are a helpful assistant who can use tools to help users with tasks
Today's date is {datetime.now().strftime("%Y-%m-%d")}

ALL RESPONSES should be in plain text and not markdown.
"""
# prompt for the main agent
prompt = ChatPromptTemplate.from_messages([
    ("system", PROMPT_TEMPLATE),
    ("placeholder", "{messages}"),
])
# Initialize the language model with your OpenAI API key
model = ChatOpenAI(model="gpt-4o", api_key=openai_api_key).bind_tools(tools)
prompted_model = prompt | model


def call_agent(state):
    """Define the agent function that invokes the model"""
    messages = state["messages"]
    # replace placeholder with messages from state
    response = prompted_model.invoke({"messages": messages})
    return {"messages": [response]}


def should_continue(state: MessagesState, config: dict):
    """Function to determine the next step based on the model's response"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        user_id = config["configurable"].get("user_id")
        tool_name = state["messages"][-1].tool_calls[0]["name"]
        auth_response = toolkit.authorize(tool_name, user_id)
        if auth_response.status == "completed":
            return "tools"
        else:
            # If the tool requires authorization, proceed to the authorization step
            return "authorization"
    # If no tool calls are present, end the workflow
    return END


def wait_for_auth(state: MessagesState):
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        return "agent"
    return "tools"


def authorize(state: MessagesState, config: dict):
    """Function to handle tool authorization"""
    user_id = config["configurable"].get("user_id")
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    auth_response = toolkit.authorize(tool_name, user_id)

    auth_message = (
        f"Please authorize the application in your browser:\n\n {auth_response.authorization_url}"
    )
    tool_call_id = state["messages"][-1].tool_calls[0]["id"]
    response = ToolMessage(
        content=auth_message,
        tool_call_id=tool_call_id,
    )
    # Add the new message to the message history and add a new human message
    # saying that the agent should try again
    try_message = HumanMessage(
        content="Please try the previous tool call again now that you are authorized."
    )
    return {"messages": [response, try_message]}


# Build the workflow graph
workflow = StateGraph(MessagesState, AgentConfigurable)

# Add nodes to the graph
workflow.add_node("agent", call_agent)
workflow.add_node("tools", tool_node)
workflow.add_node("authorization", authorize)
# workflow.add_node("wait_for_auth", wait_for_auth)

# Define the edges and control flow
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["authorization", "tools", END])
workflow.add_edge("authorization", "agent")
workflow.add_edge("tools", "agent")

# Compile the graph with an interrupt after the authorization node
# so that we can prompt the user to authorize the application
graph = workflow.compile(interrupt_after=["authorization"])
