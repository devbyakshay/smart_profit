import google.generativeai as genai
import time
from config import GEMINI_API_KEY
from logger import log_error

genai.configure(api_key=GEMINI_API_KEY)

def get_trade_decision(chart_data, retries=3, delay=5):
    """
    Analyzes chart data using the Gemini API to get a trading decision with retry logic.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Analyze the following cryptocurrency chart data and provide a trading recommendation for a scalping strategy.
    Your options are: BUY, SELL, SKIP, or CLOSE_ALL.
    Return only the decision as a single word.

    Chart Data:
    {chart_data}
    """
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            decision = response.text.strip().upper()
            if decision in ["BUY", "SELL", "SKIP", "CLOSE_ALL"]:
                return decision
            else:
                log_error(f"Invalid decision from Gemini: {decision}")
        except Exception as e:
            log_error(f"Error getting trade decision (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return "SKIP" # Default to skipping if the API fails

if __name__ == '__main__':
    # Example usage:
    example_chart_data = "BTC/USD is currently in an uptrend."
    decision = get_trade_decision(example_chart_data)
    print(f"Trade Decision: {decision}")
