import logging
from datetime import datetime

class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def setup_logger():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    return logging.getLogger(__name__)

def log_info(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{BColors.OKBLUE}[{timestamp}] [INFO] {message}{BColors.ENDC}")

def log_success(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{BColors.OKGREEN}[{timestamp}] [SUCCESS] {message}{BColors.ENDC}")

def log_warning(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.warning(f"{BColors.WARNING}[{timestamp}] [WARNING] {message}{BColors.ENDC}")

def log_error(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.error(f"{BColors.FAIL}[{timestamp}] [ERROR] {message}{BColors.ENDC}")

def log_trade(trade_type, pair, price, trade_id, amount, stop_loss, take_profit):
    color = BColors.OKGREEN if trade_type.upper() == "BUY" else BColors.FAIL
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{color}[{timestamp}] [TRADE] Opened {trade_type.upper()} trade for {pair} at ${price:.2f} (ID: {trade_id}){BColors.ENDC}")
    logging.info(f"{color}          Amount: ${amount:.2f} | Stop-Loss: ${stop_loss:.2f} | Take-Profit: ${take_profit:.2f}{BColors.ENDC}")

def log_close(trade_id, pair, profit_loss, trade_amount):
    color = BColors.OKGREEN if profit_loss >= 0 else BColors.FAIL
    result = "PROFIT" if profit_loss >= 0 else "LOSS"
    profit_percent = (profit_loss / trade_amount) * 100 if trade_amount else 0
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{color}[{timestamp}] [CLOSE] Closed trade {trade_id} for {pair}. Result: ${profit_loss:.2f} ({profit_percent:.4f}%) {result}{BColors.ENDC}")

if __name__ == '__main__':
    setup_logger()
    log_info("This is an info message.")
    log_success("This is a success message.")
    log_warning("This is a warning message.")
    log_error("This is an error message.")
    log_trade("BUY", "BTC/USD", 68000.00, "trade_001")
    log_close("trade_001", "BTC/USD", 500.00)
    log_close("trade_002", "ETH/USD", -100.00)
