"""
Reddit Personalized AI Digest Bot using Arcade with CrewAI.

This example demonstrates how to create a Reddit digest bot that:
1. Authenticates with Reddit via Arcade.dev
2. Fetches the user's personalized Reddit feed
3. Uses CrewAI agents to analyze and summarize the content
4. Generates a personalized digest

Requirements:
1. An Arcade API key (set as ARCADE_API_KEY environment variable)
2. An OpenAI API key (set as OPENAI_API_KEY environment variable)
3. Install dependencies: `pip install crewai crewai-arcade langchain langchain-openai python-dotenv`
"""

from typing import Any, Dict, List
import os
import json
from datetime import datetime

from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai.crews import CrewOutput
from crewai.llm import LLM
from crewai_arcade import ArcadeToolManager

# Load environment variables
load_dotenv()

# Unique user identifier for Arcade
USER_ID = os.getenv("USER_ID", "reddit-digest-user")

def custom_auth_flow(
    manager: ArcadeToolManager, tool_name: str, **tool_input: dict[str, Any]
) -> Any:
    """Custom authorization flow for Reddit tools via Arcade"""
    # Check if user is already authorized
    auth_response = manager.authorize(tool_name, USER_ID)
    
    # If not authorized, handle the authentication
    if not manager.is_authorized(auth_response.id):
        print(f"\n🔐 Authorization required for {tool_name}")
        print(f"📱 Please visit this URL to authenticate with Reddit: {auth_response.url}")
        print("⏳ Waiting for authentication to complete...")
        
        # Wait for user to complete authentication
        auth_response = manager.wait_for_auth(auth_response)
        
        # Verify authentication was successful
        if not manager.is_authorized(auth_response.id):
            raise ValueError(f"❌ Authentication failed for {tool_name}. URL: {auth_response.url}")
        
        print("✅ Authentication successful!")
    else:
        print(f"✅ Already authenticated for {tool_name}")

def custom_execute_flow(
    manager: ArcadeToolManager, tool_name: str, **tool_input: dict[str, Any]
) -> Any:
    """Custom execution flow for Reddit tools via Arcade"""
    print(f"\n🚀 Executing {tool_name} with inputs:")
    for input_name, input_value in tool_input.items():
        print(f"  - {input_name}: {input_value}")
    
    # Execute the tool via Arcade
    response = manager._client.tools.execute(
        tool_name=tool_name,
        input=tool_input,
        user_id=USER_ID,
    )
    
    # Handle any errors
    tool_error = response.output.error if response.output else None
    if tool_error:
        print(f"❌ Error executing {tool_name}: {tool_error}")
        return str(tool_error)
    
    # Return the successful result
    if response.success:
        print(f"✅ Successfully executed {tool_name}")
        return response.output.value
    
    # Default error message
    return f"Failed to execute {tool_name}"

def custom_tool_executor(
    manager: ArcadeToolManager, tool_name: str, **tool_input: dict[str, Any]
) -> Any:
    """Custom tool executor that handles auth and execution"""
    custom_auth_flow(manager, tool_name, **tool_input)
    return custom_execute_flow(manager, tool_name, **tool_input)

def main() -> CrewOutput:
    """Main function to run the Reddit Digest Bot"""
    print("🤖 Starting Reddit Personalized AI Digest Bot")
    
    # Initialize Arcade Tool Manager with custom executor
    manager = ArcadeToolManager(
        executor=custom_tool_executor,
    )
    
    # Get Reddit tools via Arcade
    reddit_tools = manager.get_tools(tools=["Reddit.GetSubscribedSubreddits", "Reddit.GetSubredditHotPosts"])
    
    # Initialize language model
    llm = LLM(model="gpt-4o", temperature=0.5)
    
    # Create the agents
    fetcher_agent = Agent(
        role="Reddit Data Fetcher",
        goal="Collect and organize user's Reddit content",
        backstory="""You are an expert at navigating Reddit's structure and content. 
        Your job is to fetch the user's subscribed subreddits and collect the most relevant
        posts from each to provide a comprehensive view of their Reddit feed.""",
        tools=reddit_tools,
        verbose=True,
        llm=llm,
    )
    
    analyzer_agent = Agent(
        role="Content Analyzer",
        goal="Analyze and categorize Reddit content",
        backstory="""You are a content analysis expert who excels at identifying patterns,
        themes, and categories across diverse content. Your job is to organize Reddit posts
        into meaningful groups that make sense for the user.""",
        verbose=True,
        llm=llm,
    )
    
    summarizer_agent = Agent(
        role="Digest Creator",
        goal="Create an engaging, informative digest",
        backstory="""You are a skilled writer and communicator who knows how to distill complex
        information into clear, engaging summaries. Your job is to create a personalized Reddit
        digest that highlights the most interesting and relevant content.""",
        verbose=True,
        llm=llm,
    )
    
    # Create tasks
    fetch_task = Task(
        description="""
        Fetch the user's subscribed subreddits and then get the hot posts from each subreddit.
        
        Steps:
        1. Use Reddit.GetSubscribedSubreddits to get the list of subreddits the user subscribes to
        2. For each subreddit (up to 10 maximum), use Reddit.GetSubredditHotPosts to fetch the hot posts (limit 5 posts per subreddit)
        3. Organize the data into a structured format that includes:
           - Subreddit name
           - Post title
           - Post score
           - Number of comments
           - Post URL
           - Brief preview of content if available
        
        Return the data as a JSON structure.
        """,
        expected_output="A JSON object containing the user's subreddit subscriptions and hot posts from each",
        agent=fetcher_agent,
    )
    
    analyze_task = Task(
        description="""
        Analyze the Reddit data to identify patterns and categorize content.
        
        Steps:
        1. Review the Reddit posts from all subreddits
        2. Identify 4-6 meaningful categories based on:
           - Topics (news, humor, technology, etc.)
           - Content type (discussion, media, question, announcement)
           - User engagement level
           - Common themes across different subreddits
        3. Assign each post to the most appropriate category
        4. For each category, identify the top 2-3 posts based on relevance and engagement
        
        Return a structured analysis with categories and their top posts.
        """,
        expected_output="A structured analysis of the Reddit content with categorization",
        agent=analyzer_agent,
        context=[fetch_task],
    )
    
    summary_task = Task(
        description="""
        Create a personalized Reddit digest based on the analyzed content.
        
        The digest should:
        1. Start with a brief, friendly introduction
        2. Present each category with:
           - A descriptive category name
           - A brief overview of what this category contains
           - Summaries of the top 2-3 posts with titles and links
           - Any notable trends or discussions in this category
        3. End with a brief conclusion
        
        Format the digest in Markdown for readability, with clear headings, bullet points, and links.
        Make it personal, engaging, and easy to skim.
        """,
        expected_output="A complete, well-formatted Reddit digest in Markdown",
        agent=summarizer_agent,
        context=[analyze_task],
    )
    
    # Create and run the crew
    crew = Crew(
        agents=[fetcher_agent, analyzer_agent, summarizer_agent],
        tasks=[fetch_task, analyze_task, summary_task],
        verbose=True,
    )
    
    # Kickoff the crew
    result = crew.kickoff()
    
    # Format the results
    print("\n\n🎯 Creating your personalized Reddit digest...\n")
    
    # Save the digest to a file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"reddit_digest_{timestamp}.md"
    
    with open(filename, "w") as f:
        f.write(result.raw_output)
    
    print(f"\n✅ Digest saved to {filename}")
    
    return result

if __name__ == "__main__":
    result = main()
    print("\n\n----------------- YOUR REDDIT DIGEST -----------------\n")
    print(result.raw_output)
    print("\n-----------------------------------------------------\n")