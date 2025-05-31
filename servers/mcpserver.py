from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP()

#### Tools ####
# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print(f"Adding {a} and {b}")
    return a + b


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')
