# Stock Market Analysis MCP

Welcome to the Stock Market Analysis project, powered by [crewAI](https://crewai.com). This project provides a sophisticated stock market analysis system that leverages AI agents to analyze market data, technical indicators, and market sentiment.

## Features

- **Comprehensive Market Analysis**
  - Historical price data analysis
  - Technical indicators (RSI, ATR, MFI)
  - Market sentiment analysis
  - Summary statistics and performance metrics

- **Technical Indicators**
  - RSI (Relative Strength Index) for overbought/oversold conditions
  - ATR (Average True Range) for volatility measurement
  - MFI (Money Flow Index) for volume-weighted price analysis

- **Market Sentiment Analysis**
  - News sentiment analysis
  - Social media sentiment tracking
  - Top headlines and market impact analysis

## Installation

Ensure you have Python >=3.10 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

First, install uv:
```bash
pip install uv
```

Next, install the project dependencies:
```bash
crewai install
```

### Configuration

1. Add your `OPENAI_API_KEY` to the `.env` file
2. The MCP server provides two main tools:
   - `basicdata`: Fetches comprehensive market data and technical indicators
   - `sentimentdata`: Analyzes market sentiment from news and social media

## Running the Project

1. Start the MCP server:
```bash
python servers/newmcpserver.py
```

2. Run the analysis:
```bash
python test.py
```

This will:
- Initialize a stock market expert agent
- Analyze the specified stock (default: RELIANCE)
- Generate a detailed analysis report in `analysis.md`

## Understanding the Analysis

The system provides comprehensive market analysis including:

1. **Summary Statistics**
   - Average daily returns
   - Price volatility
   - Maximum drawdown

2. **Technical Indicators**
   - RSI signals (buy/sell/hold)
   - ATR for volatility measurement
   - MFI for money flow analysis

3. **Market Sentiment**
   - News sentiment scores
   - Social media sentiment
   - Top market headlines

## Example Usage

```python
from crewai_tools import MCPServerAdapter
from crewai import Agent, Task, Crew

# Initialize the MCP server connection
server_params = {"url": "http://localhost:8000/sse"}

# Create and run the analysis
with MCPServerAdapter(server_params) as tools:
    agent = Agent(
        role="Stock Market Expert",
        goal="Analyze market data and generate insights",
        tools=tools
    )
    task = Task(
        description="Analyze RELIANCE stock for the period 2025-01-01 to 2025-01-30",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
```

## Support

For support or questions:
- Visit our [documentation](https://docs.crewai.com)
- Reach out through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
