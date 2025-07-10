import schedule
import time
import json
import uuid
from datetime import datetime
from threading import Thread, Lock
from gemini_client import get_trade_decision
from crypto_client import get_crypto_price, get_historical_prices, get_atr
from logger import log_info, log_success, log_warning, log_error, log_trade, log_close, setup_logger
from config import MAX_ONGOING_TRADES, RISK_PER_TRADE, ATR_MULTIPLIER_SL, ATR_MULTIPLIER_TP, TRADE_COOLDOWN

DATABASE_FILE = 'database.json'

db_lock = Lock()

def read_database():
    with db_lock:
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)

def write_database(data):
    with db_lock:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

def get_chart_data(current_price, ongoing_trades):
    """
    Generates a chart data summary to be sent to the Gemini API.
    """
    historical_prices = get_historical_prices(days=1)
    if not historical_prices:
        return f"Current price of BTC/USD is {current_price}. No historical data available."

    # Simple trend analysis
    price_start = historical_prices[0]
    price_end = historical_prices[-1]
    trend = "upward" if price_end > price_start else "downward"
    
    # Simple volatility
    price_change = (price_end - price_start) / price_start * 100
    volatility = "high" if abs(price_change) > 5 else "low"

    ongoing_trades_summary = "No ongoing trades."
    if ongoing_trades:
        ongoing_trades_summary = "Ongoing Trades:\n"
        for trade in ongoing_trades:
            pnl_percent = (trade.get('profit_loss', 0) / trade['amount']) * 100
            ongoing_trades_summary += (
                f"- Type: {trade['type']}, Entry: ${trade['entry_price']:.2f}, "
                f"P&L: ${trade.get('profit_loss', 0):.2f} ({pnl_percent:.4f}%)\n"
            )

    chart_summary = (
        f"Here is the summary for BTC/USD:\n"
        f"- The current price is ${current_price:.2f}.\n"
        f"- Over the last 24 hours, the price trend has been {trend}.\n"
        f"- The price has changed by {price_change:.2f}% in the last 24 hours, indicating {volatility} volatility.\n"
        f"- {ongoing_trades_summary}\n\n"
        f"Based on this data, what is your scalping decision? Your options are: BUY, SELL, SKIP, or CLOSE_ALL."
    )
    return chart_summary

def update_profit_loss():
    while True:
        try:
            data = read_database()
            current_price = get_crypto_price()
            if not current_price:
                time.sleep(30)
                continue
                
            data['current_prices']['BTC/USD'] = current_price
            
            total_pnl = 0
            for trade in data['ongoing_trades']:
                units = trade['amount'] / trade['entry_price']
                if trade['type'] == 'buy':
                    pnl = (current_price - trade['entry_price']) * units
                else: # sell
                    pnl = (trade['entry_price'] - current_price) * units
                trade['profit_loss'] = pnl
                total_pnl += pnl
            
            opening_balance = data['portfolio']['opening_balance']
            # Note: current_balance should reflect the opening balance plus realized and unrealized P&L
            # For simplicity, we'll represent it as opening + unrealized P&L of ongoing trades
            data['portfolio']['current_balance'] = opening_balance + total_pnl
            
            write_database(data)
            log_info(f"Live P&L updated. Total P&L: ${total_pnl:.2f}. Current Balance: ${data['portfolio']['current_balance']:.2f}")
        except Exception as e:
            log_error(f"An error occurred in the P&L update loop: {e}")
        time.sleep(30)

# Add a global variable for trade cooldown
last_trade_time = 0

def simulate_trade_execution():
    while True:
        try:
            data = read_database()
            trades_to_remove = []
            current_price = data['current_prices'].get('BTC/USD')

            if not current_price:
                time.sleep(1)
                continue

            for trade in data['ongoing_trades']:
                units = trade['amount'] / trade['entry_price']
                close_trade = False
                final_pnl = 0

                if trade['type'] == 'buy':
                    if current_price <= trade['stop_loss']:
                        final_pnl = (current_price - trade['entry_price']) * units
                        close_trade = True
                        log_warning(f"Stop-loss triggered for trade {trade['trade_id']}.")
                    elif current_price >= trade['take_profit']:
                        final_pnl = (current_price - trade['entry_price']) * units
                        close_trade = True
                        log_success(f"Take-profit triggered for trade {trade['trade_id']}.")
                elif trade['type'] == 'sell':
                    if current_price >= trade['stop_loss']:
                        final_pnl = (trade['entry_price'] - current_price) * units
                        close_trade = True
                        log_warning(f"Stop-loss triggered for trade {trade['trade_id']}.")
                    elif current_price <= trade['take_profit']:
                        final_pnl = (trade['entry_price'] - current_price) * units
                        close_trade = True
                        log_success(f"Take-profit triggered for trade {trade['trade_id']}.")

                if close_trade:
                    # Update balances upon closing a trade
                    data['portfolio']['opening_balance'] += final_pnl # Realized P&L is added to the opening balance
                    data['portfolio']['current_balance'] = data['portfolio']['opening_balance'] # Reset current balance to new opening balance
                    data['portfolio']['available_balance'] += trade['amount'] + final_pnl
                    trades_to_remove.append(trade)
                    log_close(trade['trade_id'], trade['pair'], final_pnl, trade['amount'])
                    
                    global last_trade_time
                    last_trade_time = time.time()


            if trades_to_remove:
                data['ongoing_trades'] = [t for t in data['ongoing_trades'] if t not in trades_to_remove]
                write_database(data)
        except Exception as e:
            log_error(f"An error occurred in the trade execution loop: {e}")
        time.sleep(1)

def trading_cycle():
    global last_trade_time
    if time.time() - last_trade_time < TRADE_COOLDOWN:
        log_info("In trade cooldown period. Skipping cycle.")
        return

    log_info("Starting new trading cycle...")
    data = read_database()

    if len(data['ongoing_trades']) >= MAX_ONGOING_TRADES:
        log_warning("Max trades reached. Skipping cycle.")
        return

    price = data['current_prices'].get('BTC/USD')
    if not price or price == 0:
        log_error("Could not get a valid price, skipping cycle.")
        return
        
    atr = get_atr()
    if not atr:
        log_error("Could not calculate ATR, skipping cycle.")
        return

    # Dynamic Position Sizing
    trade_amount = data['portfolio']['available_balance'] * RISK_PER_TRADE
    if data['portfolio']['available_balance'] < trade_amount:
        log_warning(f"Insufficient available balance for dynamic trade amount. Available: ${data['portfolio']['available_balance']:.2f}, Required: ${trade_amount:.2f}")
        return

    chart_data = get_chart_data(price, data['ongoing_trades'])
    decision = get_trade_decision(chart_data)
    log_info(f"Gemini decision: {decision}")

    if decision == "BUY" or decision == "SELL":
        trade_id = f"trade_{uuid.uuid4()}"
        
        # Dynamic Stop-Loss and Take-Profit
        if decision == "BUY":
            stop_loss = price - (atr * ATR_MULTIPLIER_SL)
            take_profit = price + (atr * ATR_MULTIPLIER_TP)
        else: # SELL
            stop_loss = price + (atr * ATR_MULTIPLIER_SL)
            take_profit = price - (atr * ATR_MULTIPLIER_TP)
        
        new_trade = {
            "trade_id": trade_id,
            "pair": "BTC/USD",
            "type": decision.lower(),
            "entry_price": price,
            "amount": trade_amount,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "profit_loss": 0,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        data['ongoing_trades'].append(new_trade)
        
        # Update balance
        data['portfolio']['available_balance'] -= trade_amount
        
        write_database(data)
        log_trade(decision, "BTC/USD", price, trade_id, trade_amount, stop_loss, take_profit)
        log_info(f"Updated available balance: ${data['portfolio']['available_balance']:.2f}")
    elif decision == "SKIP":
        log_info("Gemini decided to SKIP this trading cycle.")
    elif decision == "CLOSE_ALL":
        log_info("Gemini decided to CLOSE ALL ongoing trades.")
        trades_to_close = list(data['ongoing_trades']) # Create a copy to iterate
        for trade in trades_to_close:
            # Simulate closing the trade immediately
            current_price_at_close = data['current_prices'].get(trade['pair'])
            if current_price_at_close:
                units = trade['amount'] / trade['entry_price']
                if trade['type'] == 'buy':
                    final_pnl = (current_price_at_close - trade['entry_price']) * units
                else: # sell
                    final_pnl = (trade['entry_price'] - current_price_at_close) * units
                
                data['portfolio']['opening_balance'] += final_pnl
                data['portfolio']['current_balance'] = data['portfolio']['opening_balance']
                data['portfolio']['available_balance'] += trade['amount'] + final_pnl
                
                data['ongoing_trades'].remove(trade) # Remove from the original list
                log_close(trade['trade_id'], trade['pair'], final_pnl)
                log_info(f"Updated available balance after closing: ${data['portfolio']['available_balance']:.2f}")
        write_database(data)
        global last_trade_time
        last_trade_time = time.time() # Apply cooldown after closing all trades

if __name__ == '__main__':
    try:
        setup_logger()
        log_info("Starting trading bot...")
        
        # Start the trade execution and P&L update threads
        pnl_thread = Thread(target=update_profit_loss, daemon=True)
        pnl_thread.start()
        log_info("Live P&L updater started.")

        simulator_thread = Thread(target=simulate_trade_execution, daemon=True)
        simulator_thread.start()
        log_info("Trade execution simulator started.")

        # Schedule the trading cycle to run every 10 minutes
        schedule.every(10).minutes.do(trading_cycle)

        # Initial run
        time.sleep(5) # Give some time for the first price update
        trading_cycle()

        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log_info("Trading bot stopped by user.")
    except Exception as e:
        log_error(f"A critical error occurred in the main loop: {e}")
