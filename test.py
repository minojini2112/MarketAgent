from crewai_tools import MCPServerAdapter
from crewai import Agent, Task, Crew

server_params = {"url": "http://localhost:8000/sse"}

with MCPServerAdapter(server_params) as tools:
    print(f"Available tools from SSE MCP server: {[tool.name for tool in tools]}")

    # Example: Using the tools from the SSE MCP server in a CrewAI Agent
    agent = Agent(
        role="you are an stock market expert",
        goal="to use all available mcp tools and the data got from the mcp tool and make a report about the stock market",
        backstory="An AI that can analyze stock market problems via an MCP tool.",
        tools=tools,
        verbose=True,
    )
    task = Task(
        description="give a detailed analysis of the stock market , for the company JIOFINANCE  during the period 2025-01-01 to 2025-01-30",
        expected_output="analysis.md file , remove ```",
        output_file="analysis.md",
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )
    result = crew.kickoff()
    print(result)