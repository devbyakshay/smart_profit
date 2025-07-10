import requests
import time
import numpy as np
from config import COINGECKO_API_KEY
from logger import log_error, log_info

def get_atr(coin_id='bitcoin', days=14):
    """
    Calculates the Average True Range (ATR) as a measure of volatility.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    headers = {"x-cg-demo-api-key": COINGECKO_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = data['prices']
        highs = [p[1] for p in prices] # Using price as a proxy for high/low/close
        lows = [p[1] for p in prices]
        closes = [p[1] for p in prices]

        tr_list = []
        for i in range(1, len(prices)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            tr_list.append(tr)
        
        if not tr_list:
            return None
            
        return np.mean(tr_list)

    except Exception as e:
        log_error(f"Error calculating ATR: {e}")
        return None

def get_historical_prices(coin_id='bitcoin', days=1):
    """
    Fetches historical price data for a cryptocurrency from CoinGecko.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
    headers = {
        "x-cg-demo-api-key": COINGECKO_API_KEY
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Return a simplified list of prices
        return [item[1] for item in data['prices']]
    except requests.exceptions.RequestException as e:
        log_error(f"Error fetching historical price data: {e}")
        return None
    except (KeyError, ValueError) as e:
        log_error(f"Error parsing historical price data: {e}")
        return None

def get_crypto_price(coin_id='bitcoin', retries=3, delay=5):
    """
    Fetches the current price of a cryptocurrency from CoinGecko with retry logic.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    headers = {
        "x-cg-demo-api-key": COINGECKO_API_KEY
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            return data[coin_id]['usd']
        except requests.exceptions.RequestException as e:
            log_error(f"Error fetching crypto price (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
        except (KeyError, ValueError) as e:
            log_error(f"Error parsing price data: {e}")
            return None
    return None

if __name__ == '__main__':
    price = get_crypto_price()
    if price:
        print(f"The current price of Bitcoin is: ${price}")
