import os

from configuration import AgentConfigurable
from langchain_arcade import ArcadeToolManager
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

# Initialize the Arcade Tool Manager with your API key
arcade_api_key = os.getenv("ARCADE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

toolkit = ArcadeToolManager(api_key=arcade_api_key)
# Retrieve tools compatible with LangGraph
tools = toolkit.get_tools(langgraph=True)
tool_node = ToolNode(tools)

# Initialize the language model with your OpenAI API key
model = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
# make the model aware of the tools
model_with_tools = model.bind_tools(tools)


# Define the agent function that invokes the model
def call_agent(state):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    # Return the updated message history
    return {"messages": [*messages, response]}


# Function to determine the next step based on the model's response
def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        tool_name = last_message.tool_calls[0]["name"]
        if toolkit.requires_auth(tool_name):
            # If the tool requires authorization, proceed to the authorization step
            return "authorization"
        else:
            # If no authorization is needed, proceed to execute the tool
            return "tools"
    # If no tool calls are present, end the workflow
    return END


def should_wait_for_authorization(state: MessagesState):
    """Determine if the tool call required auth and if we are waiting for authorization."""
    last_message = state["messages"][-1]
    # if there is no AIMessage with auth url and instead just a tool call
    # we should proceed to "tools"
    if last_message.tool_calls:
        return "tools"
    # if there is an AIMessage with auth url, we should wait for authorization
    return "wait_for_authorization"


# Function to handle tool authorization
def authorize(state: MessagesState, config: dict):
    user_id = config["configurable"].get("user_id")
    tool_name = state["messages"][-1].tool_calls[0]["name"]
    auth_response = toolkit.authorize(tool_name, user_id)

    if auth_response.status == "completed":
        # Authorization is complete; proceed to the next step
        return {"messages": state["messages"]}
    else:
        # Create the authorization message with an HTML link
        auth_message = (
            f"Please authorize the application in your browser: {auth_response.authorization_url}"
        )

        # Put the authorization message in the logs
        print("Authorize: ", auth_response.authorization_url)

        # Add the new message to the message history
        messages = state["messages"]
        messages.append(AIMessage(content=auth_message))
        return {"messages": messages}


def wait_for_authorization(state: MessagesState):
    # Remove the authorization message from the message history
    # so that when we route to tools, the tool call is the latest one
    state["messages"].pop()
    return {"messages": state["messages"]}


# Build the workflow graph
workflow = StateGraph(MessagesState, AgentConfigurable)

# Add nodes to the graph
workflow.add_node("agent", call_agent)
workflow.add_node("tools", tool_node)
workflow.add_node("authorization", authorize)
workflow.add_node("wait_for_authorization", wait_for_authorization)
# Define the edges and control flow
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["authorization", "tools", END])
workflow.add_conditional_edges(
    "authorization", should_wait_for_authorization, ["wait_for_authorization", "tools"]
)
workflow.add_edge("wait_for_authorization", "tools")
workflow.add_edge("tools", "agent")

# Compile the graph with an interrupt after the authorization node
# so that we can prompt the user to authorize the application
graph = workflow.compile(interrupt_after=["authorization"])
