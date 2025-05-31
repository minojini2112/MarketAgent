import new
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP()

#### Tools ####
# Add an addition tool
@mcp.tool()
def basicdata(company:list,start_date:str,end_date:str):
    """
    Fetches and analyzes comprehensive market data for given companies, including price data,
    technical indicators, and statistical metrics.

    Args:
        company (list): List of company symbols (e.g., ['RELIANCE', 'TCS'])
        start_date (str): Start date in 'YYYY-MM-DD' format (the difference between the start and end date should be 30 days)
        end_date (str): End date in 'YYYY-MM-DD' format (the difference between the start and end date should be 30 days)

    Returns:
        list: A list containing 5 elements in the following order:
            [0] Summary Statistics (dict):
                Key: Company symbol
                Value: dict containing:
                    - avg_return (float): Average daily return (percentage)
                        * Positive value indicates upward trend
                        * Negative value indicates downward trend
                        * Example: 0.0015 means 0.15% average daily return
                    
                    - volatility (float): Price volatility (standard deviation of returns)
                        * Higher value indicates more price fluctuation
                        * Lower value indicates more stable price movement
                        * Example: 0.0250 means 2.50% daily volatility
                    
                    - max_drawdown (float): Maximum drawdown (largest peak-to-trough decline)
                        * Higher value indicates higher risk
                        * Example: 0.1500 means 15% maximum decline from peak

            [1] RSI Signals (list of dict):
                Each dict contains:
                    - symbol (str): Company symbol
                    - date (str): Date in 'YYYY-MM-DD' format
                    - rsi (float): Relative Strength Index (0-100)
                        * RSI > 70: Overbought condition (potential sell signal)
                        * RSI < 30: Oversold condition (potential buy signal)
                        * RSI 30-70: Neutral condition
                    - signal (int): Trading signal
                        * 1: Buy signal (RSI < 30)
                        * -1: Sell signal (RSI > 70)
                        * 0: Hold signal (RSI between 30-70)

            [2] ATR Results (dict):
                Key: Company symbol
                Value: list of dict containing:
                    - date (str): Date in 'YYYY-MM-DD' format
                    - atr (float): Average True Range (absolute price volatility)
                        * Higher ATR indicates higher volatility
                        * Used to set stop-loss levels (typically 2-3x ATR)
                    - atr_percent (float): ATR as percentage of price
                        * Example: 1.01 means 1.01% of current price

            [3] MFI Results (dict):
                Key: Company symbol
                Value: list of dict containing:
                    - date (str): Date in 'YYYY-MM-DD' format
                    - mfi (float): Money Flow Index (0-100)
                        * MFI > 80: Overbought condition
                        * MFI < 20: Oversold condition
                        * MFI 20-80: Neutral condition
                    - typical_price (float): (high + low + close) / 3
                    - money_flow (float): typical_price * volume
                        * Higher value indicates stronger buying/selling pressure

    Example:
        >>> data = basicdata(['RELIANCE'], '2025-01-01', '2025-01-10')
        >>> stats = data[0]       # Summary statistics
        >>> rsi = data[1]         # RSI signals
        >>> atr = data[2]         # ATR results
        >>> mfi = data[3]         # MFI results

    Raw Output Format Example:
        [            
            # [0] Summary Statistics
            {
                'RELIANCE': {
                    'avg_return': 0.0015,    # 0.15% average daily return
                    'volatility': 0.0250,    # 2.50% daily volatility
                    'max_drawdown': 0.1500   # 15% maximum decline
                }
            },
            
            # [1] RSI Signals
            [
                {
                    'symbol': 'RELIANCE',
                    'date': '2025-01-01',
                    'rsi': 65.50,           # Neutral RSI (30-70)
                    'signal': 0             # Hold signal
                }
            ],
            
            # [2] ATR Results
            {
                'RELIANCE': [
                    {
                        'date': '2025-01-01',
                        'atr': 25.50,        # Absolute volatility
                        'atr_percent': 1.01  # 1.01% of price
                    }
                ]
            },
            
            # [3] MFI Results
            {
                'RELIANCE': [
                    {
                        'date': '2025-01-01',
                        'mfi': 75.50,        # Neutral MFI (20-80)
                        'typical_price': 2525.50,
                        'money_flow': 3788250000
                    }
                ]
            }
        ]
    """
    return_data=[]
    data=new.fetch_historical_nse_data(company, start_date, end_date)
    stats=new.compute_summary_statistics(data)
    rsi_signals=new.generate_rsi_signals(data)
    atr_results=new.calculate_atr(data)
    mfi_results=new.calculate_money_flow_index(data)
    return_data.append(stats)
    return_data.append(rsi_signals)
    return_data.append(atr_results)
    return_data.append(mfi_results)
    return return_data

@mcp.tool()
def sentimentdata(company:list,start_date:str,end_date:str):    
    '''
    Fetches market sentiment data from news headlines and social media for given symbols.
    This is a placeholder function that simulates sentiment data collection.

    Args:
        symbols (list of str): List of stock symbols to analyze
        start_date (str): Start date in 'YYYY-MM-DD' format (the difference between the start and end date should be 30 days)
        end_date (str): End date in 'YYYY-MM-DD' format (the difference between the start and end date should be 30 days)

    Returns:
        dict: {
            'symbol': {
                'date': str,
                'news_sentiment': float,  # -1 to 1 (negative to positive)
                    * -1.0: Extremely negative sentiment
                    * -0.5: Moderately negative sentiment
                    * 0.0: Neutral sentiment
                    * 0.5: Moderately positive sentiment
                    * 1.0: Extremely positive sentiment
                'social_sentiment': float,  # -1 to 1 (negative to positive)
                    * Same scale as news_sentiment
                'news_count': int,  # Number of news articles analyzed
                'social_mentions': int,  # Number of social media mentions
                'top_headlines': list of str  # Most relevant news headlines
            }
        }
    '''

    sentiment_data = new.fetch_market_sentiment(company, start_date, end_date)
    return sentiment_data



if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')