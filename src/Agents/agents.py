import os
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
load_dotenv()

# Initialize the agents with optimized parameters for comprehensive scenario generation
qa_agent = Agent(
    model=OpenAIChat(
        id="gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY"),
        max_tokens=8000,  # Limit output token count
        temperature=0.3   # Lower temperature for more concise output
    ),
    markdown=True,
)

code_gen_agent = Agent(
    model=OpenAIChat(
        id="gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY"),
        max_tokens=8000,  # Limit output token count
        temperature=0.2   # Lower temperature for more focused code generation
    ),
    markdown=True,
) 