import yfinance as yf
from datetime import datetime, timedelta
from collections import defaultdict
import math


def fetch_historical_nse_data(symbols, start_date, end_date):
    """
    Fetches historical OHLCV data from NSE of India and returns a list of simple dicts.

    Args:
        symbols (list of str): NSE ticker symbols (e.g., ['RELIANCE', 'TCS' , 'JIOFIN']).
        start_date (str): Start date in 'YYYY-MM-DD'.
        end_date (str): End date in 'YYYY-MM-DD'.

    Returns:
        list of dict: Each dict has keys: 'symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'.
    """
    tickers = [sym if sym.endswith('.NS') else f"{sym}.NS" for sym in symbols]
    yf_end = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    data = yf.download(
        tickers,
        start=start_date,
        end=yf_end,
        group_by='ticker',
        auto_adjust=False,
        progress=False
    )
    results = []
    if data.empty:
        return results
    for ticker in tickers:
        if ticker not in data:
            continue
        df = data[ticker]
        for idx, row in df.iterrows():
            results.append({
                'symbol': ticker.replace('.NS', ''),
                'date': idx.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'adj_close': float(row['Adj Close']),
                'volume': int(row['Volume'])
            })
    results.sort(key=lambda x: (x['symbol'], x['date']))
    return results


def generate_moving_average_signals(price_records, short_window=20, long_window=50):
    """
    Generates simple moving-average crossover signals from price records.

    Args:
        price_records (list of dict): Output from fetch_historical_nse_data(), with keys including 'symbol', 'date', 'close'.
        short_window (int): Window size for short-term SMA.
        long_window (int): Window size for long-term SMA.

    Returns:
        list of dict: Each dict has keys: 'symbol', 'date', 'short_sma', 'long_sma', 'signal'.
            signal = +1 (buy), -1 (sell), 0 (hold).
    """
    symbol_records = defaultdict(list)
    for rec in price_records:
        symbol_records[rec['symbol']].append(rec)
    signals = []
    for symbol, records in symbol_records.items():
        records.sort(key=lambda x: x['date'])
        closes = [r['close'] for r in records]
        dates = [r['date'] for r in records]
        short_sma = [None] * len(closes)
        long_sma = [None] * len(closes)
        for i in range(len(closes)):
            if i + 1 >= short_window:
                short_sma[i] = sum(closes[i+1-short_window:i+1]) / short_window
            if i + 1 >= long_window:
                long_sma[i] = sum(closes[i+1-long_window:i+1]) / long_window
        for i in range(len(closes)):
            s_sma = short_sma[i]
            l_sma = long_sma[i]
            sig = 0
            if s_sma is not None and l_sma is not None:
                if s_sma > l_sma:
                    sig = 1
                elif s_sma < l_sma:
                    sig = -1
            signals.append({
                'symbol': symbol,
                'date': dates[i],
                'short_sma': s_sma,
                'long_sma': l_sma,
                'signal': sig
            })
    signals.sort(key=lambda x: (x['symbol'], x['date']))
    return signals


def evaluate_signals(price_records, signals):
    """
    Evaluates trading signals to compute trade P&L and summary metrics without real execution.

    Args:
        price_records (list of dict): Historical price data.
        signals (list of dict): Output from generate_moving_average_signals().

    Returns:
        dict: {
            'trades': list of dicts {'symbol','entry_date','exit_date','entry_price','exit_price','pnl'},
            'total_pnl': float,
            'win_rate': float
        }
    """
    prices = defaultdict(dict)
    for rec in price_records:
        prices[rec['symbol']][rec['date']] = rec['close']

    trades = []
    open_positions = {}

    for sig in signals:
        sym = sig['symbol']
        date = sig['date']
        price = prices[sym].get(date)
        if price is None:
            continue
        if sig['signal'] == 1 and sym not in open_positions:
            open_positions[sym] = {'entry_date': date, 'entry_price': price}
        elif sig['signal'] == -1 and sym in open_positions:
            entry = open_positions.pop(sym)
            pnl = price - entry['entry_price']
            trades.append({
                'symbol': sym,
                'entry_date': entry['entry_date'],
                'exit_date': date,
                'entry_price': entry['entry_price'],
                'exit_price': price,
                'pnl': pnl
            })
    total_pnl = sum(t['pnl'] for t in trades)
    win_rate = sum(1 for t in trades if t['pnl'] > 0) / len(trades) if trades else 0
    return {'trades': trades, 'total_pnl': total_pnl, 'win_rate': win_rate}


def compute_summary_statistics(price_records):
    """
    Computes basic summary stats for each symbol: average daily return, volatility, max drawdown.

    Args:
        price_records (list of dict): Output from fetch_historical_nse_data().

    Returns:
        dict: { symbol: { 'avg_return': float, 'volatility': float, 'max_drawdown': float } }
    """
    stats = {}
    symbol_records = defaultdict(list)
    for rec in price_records:
        symbol_records[rec['symbol']].append(rec)
    for symbol, records in symbol_records.items():
        records.sort(key=lambda x: x['date'])
        prices = [r['close'] for r in records]
        if len(prices) < 2:
            continue
        # daily returns
        returns = [(prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
        avg_ret = sum(returns) / len(returns)
        vol = math.sqrt(sum((r-avg_ret)**2 for r in returns) / (len(returns)-1))
        # max drawdown
        peak = prices[0]
        max_dd = 0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak
            if dd > max_dd:
                max_dd = dd
        stats[symbol] = {
            'avg_return': avg_ret,
            'volatility': vol,
            'max_drawdown': max_dd
        }
    return stats


def generate_rsi_signals(price_records, period=14, overbought=70, oversold=30):
    """
    Generates trading signals based on Relative Strength Index (RSI) indicator.

    Args:
        price_records (list of dict): Output from fetch_historical_nse_data(), with keys including 'symbol', 'date', 'close'.
        period (int): RSI calculation period (default: 14 days).
        overbought (int): RSI threshold for overbought condition (default: 70).
        oversold (int): RSI threshold for oversold condition (default: 30).

    Returns:
        list of dict: Each dict has keys: 'symbol', 'date', 'rsi', 'signal'.
            signal = +1 (buy), -1 (sell), 0 (hold).
    """
    symbol_records = defaultdict(list)
    for rec in price_records:
        symbol_records[rec['symbol']].append(rec)
    
    signals = []
    for symbol, records in symbol_records.items():
        records.sort(key=lambda x: x['date'])
        closes = [r['close'] for r in records]
        dates = [r['date'] for r in records]
        
        # Calculate price changes
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        # Calculate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate RSI
        rsi_values = [None] * len(closes)
        for i in range(period, len(closes)):
            avg_gain = sum(gains[i-period:i]) / period
            avg_loss = sum(losses[i-period:i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values[i] = rsi
            
            # Generate signals
            signal = 0
            if rsi <= oversold:
                signal = 1  # Buy signal
            elif rsi >= overbought:
                signal = -1  # Sell signal
                
            signals.append({
                'symbol': symbol,
                'date': dates[i],
                'rsi': rsi,
                'signal': signal
            })
    
    signals.sort(key=lambda x: (x['symbol'], x['date']))
    return signals


def calculate_atr(price_records, period=14):
    """
    Calculates Average True Range (ATR) for risk management and position sizing.

    Args:
        price_records (list of dict): Output from fetch_historical_nse_data(), with keys including 'symbol', 'date', 'high', 'low', 'close'.
        period (int): ATR calculation period (default: 14 days).

    Returns:
        dict: { symbol: { 'date': str, 'atr': float, 'atr_percent': float } }
            atr: Absolute ATR value
            atr_percent: ATR as percentage of closing price
    """
    atr_data = {}
    symbol_records = defaultdict(list)
    
    for rec in price_records:
        symbol_records[rec['symbol']].append(rec)
    
    for symbol, records in symbol_records.items():
        records.sort(key=lambda x: x['date'])
        atr_data[symbol] = []
        
        # Calculate True Range
        tr_values = []
        for i in range(1, len(records)):
            high = records[i]['high']
            low = records[i]['low']
            prev_close = records[i-1]['close']
            
            tr1 = high - low  # Current high - current low
            tr2 = abs(high - prev_close)  # Current high - previous close
            tr3 = abs(low - prev_close)  # Current low - previous close
            
            tr = max(tr1, tr2, tr3)
            tr_values.append(tr)
        
        # Calculate ATR
        for i in range(period, len(records)):
            if i < period:
                continue
                
            # Calculate ATR using simple moving average
            atr = sum(tr_values[i-period:i]) / period
            close_price = records[i]['close']
            atr_percent = (atr / close_price) * 100  # ATR as percentage of price
            
            atr_data[symbol].append({
                'date': records[i]['date'],
                'atr': atr,
                'atr_percent': atr_percent
            })
    
    return atr_data


def calculate_money_flow_index(price_records, period=14):
    """
    Calculates Money Flow Index (MFI) which is a volume-weighted RSI that helps identify
    overbought/oversold conditions while considering trading volume.

    Args:
        price_records (list of dict): Output from fetch_historical_nse_data(), with keys including 
            'symbol', 'date', 'high', 'low', 'close', 'volume'.
        period (int): MFI calculation period (default: 14 days).

    Returns:
        dict: { symbol: { 'date': str, 'mfi': float, 'typical_price': float, 'money_flow': float } }
            mfi: Money Flow Index value (0-100)
            typical_price: (high + low + close) / 3
            money_flow: typical_price * volume
    """
    mfi_data = {}
    symbol_records = defaultdict(list)
    
    for rec in price_records:
        symbol_records[rec['symbol']].append(rec)
    
    for symbol, records in symbol_records.items():
        records.sort(key=lambda x: x['date'])
        mfi_data[symbol] = []
        
        # Calculate typical price and money flow
        typical_prices = []
        money_flows = []
        
        for record in records:
            typical_price = (record['high'] + record['low'] + record['close']) / 3
            money_flow = typical_price * record['volume']
            
            typical_prices.append(typical_price)
            money_flows.append(money_flow)
        
        # Calculate MFI
        for i in range(period, len(records)):
            if i < period:
                continue
                
            # Get the period's data
            period_tp = typical_prices[i-period:i]
            period_mf = money_flows[i-period:i]
            
            # Calculate positive and negative money flow
            positive_flow = 0
            negative_flow = 0
            
            for j in range(1, len(period_tp)):
                if period_tp[j] > period_tp[j-1]:
                    positive_flow += period_mf[j]
                else:
                    negative_flow += period_mf[j]
            
            # Calculate Money Flow Index
            if negative_flow == 0:
                mfi = 100
            else:
                money_ratio = positive_flow / negative_flow
                mfi = 100 - (100 / (1 + money_ratio))
            
            mfi_data[symbol].append({
                'date': records[i]['date'],
                'mfi': mfi,
                'typical_price': typical_prices[i],
                'money_flow': money_flows[i]
            })
    
    return mfi_data


def fetch_market_sentiment(symbols, start_date, end_date):
    """
    Fetches market sentiment data from news headlines and social media for given symbols.
    This is a placeholder function that simulates sentiment data collection.

    Args:
        symbols (list of str): List of stock symbols to analyze
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        dict: {
            'symbol': {
                'date': str,
                'news_sentiment': float,  # -1 to 1 (negative to positive)
                'social_sentiment': float,  # -1 to 1 (negative to positive)
                'news_count': int,
                'social_mentions': int,
                'top_headlines': list of str
            }
        }
    """
    import random  # For simulation purposes
    from datetime import datetime, timedelta
    
    sentiment_data = {}
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    current = start
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        for symbol in symbols:
            if symbol not in sentiment_data:
                sentiment_data[symbol] = []
            
            # Simulate sentiment data (in real implementation, this would fetch from APIs)
            news_sentiment = random.uniform(-1, 1)
            social_sentiment = random.uniform(-1, 1)
            news_count = random.randint(5, 50)
            social_mentions = random.randint(10, 200)
            
            # Simulate some sample headlines
            headlines = [
                f"{symbol} announces quarterly results",
                f"Analysts bullish on {symbol}",
                f"{symbol} expands into new markets",
                f"Market reacts to {symbol} news",
                f"{symbol} partners with tech giant"
            ]
            
            sentiment_data[symbol].append({
                'date': date_str,
                'news_sentiment': round(news_sentiment, 2),
                'social_sentiment': round(social_sentiment, 2),
                'news_count': news_count,
                'social_mentions': social_mentions,
                'top_headlines': random.sample(headlines, 3)
            })
        
        current += timedelta(days=1)
    
    return sentiment_data


def fetch_options_data(symbol, expiry_date=None):
    """
    Fetches and analyzes options data for a given stock symbol.

    Args:
        symbol (str): Stock symbol (e.g., 'RELIANCE','JIOFIN'	)
        expiry_date (str, optional): Options expiry date in 'YYYY-MM-DD' format. If None, fetches nearest expiry.

    Returns:
        dict: {
            'symbol': str,
            'expiry_date': str,
            'current_price': float,
            'calls': list of dict with keys: 'strike', 'last_price', 'bid', 'ask', 'volume', 'open_interest', 'implied_volatility',
            'puts': list of dict with keys: 'strike', 'last_price', 'bid', 'ask', 'volume', 'open_interest', 'implied_volatility',
            'put_call_ratio': float,
            'max_pain': float
        }
    """
    import random  # For simulation purposes
    
    # In real implementation, this would fetch from yfinance or other options data provider
    # For now, we'll simulate the data
    current_price = random.uniform(1000, 5000)
    
    # Generate strike prices around current price
    strikes = [round(current_price * (1 + i * 0.05)) for i in range(-5, 6)]
    
    # Generate calls data
    calls = []
    for strike in strikes:
        if strike <= current_price:
            continue
        calls.append({
            'strike': strike,
            'last_price': round(random.uniform(1, 100), 2),
            'bid': round(random.uniform(1, 100), 2),
            'ask': round(random.uniform(1, 100), 2),
            'volume': random.randint(100, 1000),
            'open_interest': random.randint(1000, 5000),
            'implied_volatility': round(random.uniform(0.2, 0.8), 2)
        })
    
    # Generate puts data
    puts = []
    for strike in strikes:
        if strike >= current_price:
            continue
        puts.append({
            'strike': strike,
            'last_price': round(random.uniform(1, 100), 2),
            'bid': round(random.uniform(1, 100), 2),
            'ask': round(random.uniform(1, 100), 2),
            'volume': random.randint(100, 1000),
            'open_interest': random.randint(1000, 5000),
            'implied_volatility': round(random.uniform(0.2, 0.8), 2)
        })
    
    # Calculate put-call ratio
    total_put_volume = sum(put['volume'] for put in puts)
    total_call_volume = sum(call['volume'] for call in calls)
    put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else float('inf')
    
    # Calculate max pain (strike price with highest open interest)
    all_strikes = [(put['strike'], put['open_interest']) for put in puts] + \
                 [(call['strike'], call['open_interest']) for call in calls]
    max_pain = max(all_strikes, key=lambda x: x[1])[0] if all_strikes else current_price
    
    return {
        'symbol': symbol,
        'expiry_date': expiry_date or '2025-01-15',  # Simulated expiry date
        'current_price': round(current_price, 2),
        'calls': calls,
        'puts': puts,
        'put_call_ratio': round(put_call_ratio, 2),
        'max_pain': max_pain
    }

# Example usage:
#data = fetch_historical_nse_data(['JIOFIN'], '2025-01-01', '2025-05-30')
#print(data)
'''stats = compute_summary_statistics(data)
print(stats)
print(type(data))
# Generate RSI signals
rsi_signals = generate_rsi_signals(data)
# Evaluate the signals
results = evaluate_signals(data, rsi_signals)
print(f"Total P&L: {results['total_pnl']}")
print(f"Win Rate: {results['win_rate']:.2%}")

# Calculate ATR
atr_results = calculate_atr(data)
# Print results for each symbol
for symbol, values in atr_results.items():
    print(f"\nATR for {symbol}:")
    print(f"Latest ATR: {values[-1]['atr']:.2f}")
    print(f"Latest ATR%: {values[-1]['atr_percent']:.2f}%")

# Calculate MFI
mfi_results = calculate_money_flow_index(data)
# Print results for each symbol
for symbol, values in mfi_results.items():
    print(f"\nMFI for {symbol}:")
    print(f"Latest MFI: {values[-1]['mfi']:.2f}")
    print(f"Latest Typical Price: {values[-1]['typical_price']:.2f}")
    print(f"Latest Money Flow: {values[-1]['money_flow']:,.0f}")

# Example usage for sentiment data
symbols = ['RELIANCE', 'TCS' , 'JIOFIN']
start_date = '2025-01-01'
end_date = '2025-01-10'
sentiment_data = fetch_market_sentiment(symbols, start_date, end_date)

# Print sample sentiment data
for symbol in symbols:
    print(f"\nSentiment data for {symbol}:")
    for day_data in sentiment_data[symbol][:3]:  # Show first 3 days
        print(f"\nDate: {day_data['date']}")
        print(f"News Sentiment: {day_data['news_sentiment']:.2f}")
        print(f"Social Sentiment: {day_data['social_sentiment']:.2f}")
        print(f"News Count: {day_data['news_count']}")
        print(f"Social Mentions: {day_data['social_mentions']}")
        print("Top Headlines:", day_data['top_headlines'])

# Example usage for options data
options_data = fetch_options_data('JIOFIN')
print(f"\nOptions data for {options_data['symbol']}:")
print(f"Current Price: {options_data['current_price']}")
print(f"Put-Call Ratio: {options_data['put_call_ratio']}")
print(f"Max Pain: {options_data['max_pain']}")
print("\nSample Call Options:")
for call in options_data['calls'][:3]:
    print(f"Strike: {call['strike']}, Last: {call['last_price']}, IV: {call['implied_volatility']}")
print("\nSample Put Options:")
for put in options_data['puts'][:3]:
    print(f"Strike: {put['strike']}, Last: {put['last_price']}, IV: {put['implied_volatility']}")'''