# Automatic Crypto Trading Server Simulation

This project is a Python-based automatic crypto trading server that simulates scalp trading.

## Setup

1.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

2.  Make sure you have your Gemini API key in `config.py`.

## Running the Simulation

To start the trading bot, run the following command:

```bash
python3 main.py
```

The bot will then start checking for trading opportunities every 10 minutes, and the trade execution simulator will run in the background.
