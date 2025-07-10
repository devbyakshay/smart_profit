# Masterplan: Automatic Crypto Trading Server Simulation

This document outlines the masterplan for creating a Python-based automatic crypto trading server. This server will simulate scalp trading by checking for new opportunities every 10 minutes, managing ongoing trades, and simulating trade execution based on live market data from a local JSON database. Trade decisions will be powered by the Gemini API (Flash 2.0 model).

-----

## Required Things :: 

Gemini API KEY :  AIzaSyDuejEbcpCml1vCJJ-ibbJIXy_5WaNR4g8
COINGEKO API KEY : CG-o2uy83W6fxKsyHy7cCBPCNsQ	

## **1. Project Overview** 📝

The core objective is to build a simulated crypto trading bot that can:

  * **Automatically identify scalp trading opportunities** by analyzing chart patterns.
  * **Make trading decisions** using the Gemini API's analytical capabilities.
  * **Simulate trade execution** by monitoring a local JSON database that mimics real-time price movements.
  * **Manage a portfolio** by tracking ongoing trades, profits, losses, and available balance.
  * **Implement risk management** by automatically closing trades at predefined stop-loss or take-profit levels.

The entire system will operate in a simulated environment, meaning no real funds will be used.

-----

## **2. System Architecture** 🏗️

The system will consist of four main components that work in concert:

1.  **Trading Bot (Main Controller):** The central script that orchestrates the entire process. It runs on a schedule, triggers trade analysis, and manages the simulation.
2.  **Local JSON Database:** A simple file-based database (`database.json`) that acts as the single source of truth for the simulation. It will store:
      * Current account balance.
      * Ongoing trades with their entry price, stop-loss, and take-profit levels.
      * Simulated current prices of cryptocurrencies.
3.  **Gemini API Integration:** A module responsible for communicating with the Gemini API. It will send chart data (in a suitable format) and receive trading decisions.
4.  **Trade Execution Simulator:** A script that runs continuously (or every second) to check the status of open trades against the simulated market prices in the JSON database.

### **Architectural Diagram**

```mermaid
graph TD
    A[Trading Bot - main.py] -->|Checks every 10 mins| B{New Trade Opportunity?};
    B -- Yes --> C[Gemini API Integration];
    C -- Analyzes Chart Data --> D[Receives Trade Decision];
    D -- Profitable Trade & Capacity --> E[Opens New Trade];
    E -- Updates --> F[Local JSON Database - database.json];
    B -- No --> A;

    G[Trade Execution Simulator - simulator.py] -- Runs every second --> F;
    F -- Reads Open Trades & Prices --> G;
    G -- Price hits SL/TP? --> H{Close Trade};
    H -- Yes --> F;
```

-----

## **3. Core Components** ⚙️

### **3.1. Trading Bot (`main.py`)**

  * **Scheduler:** Will use a library like `schedule` to run the main trading logic every 10 minutes.
  * **Trade Capacity Check:** Before seeking a new trade, it will check the number of `ongoing_trades`. If the number exceeds a predefined limit (`x`), it will attempt to close a profitable trade.
      * If a profitable trade is found and closed, it proceeds to look for a new trade.
      * If no profitable trades can be closed, it skips the current trading cycle.
  * **Data Preparation:** It will read the latest simulated chart data (this could be pre-defined patterns or fetched from an external source for realism) and format it for the Gemini API.
  * **Trade Initiation:** Upon receiving a "buy" or "sell" signal from the Gemini API, it will create a new trade entry in the `database.json` file.

### **3.2. Local JSON Database (`database.json`)**

This file will have a simple structure:

```json
{
  "account_balance": 10000.0,
  "ongoing_trades": [
    {
      "trade_id": "trade_001",
      "pair": "BTC/USD",
      "type": "buy",
      "entry_price": 68000.0,
      "stop_loss": 67800.0,
      "take_profit": 68500.0,
      "timestamp": "2025-07-11T12:00:00Z"
    }
  ],
  "current_prices": {
    "BTC/USD": 68250.5
  }
}
```

### **3.3. Gemini API Integration (`gemini_client.py`)**

  * **API Key Management:** Securely store and use the Gemini API key.
  * **Prompt Engineering:** Design a clear and concise prompt to send to the Gemini Flash 2.0 model. The prompt will include the chart data and ask for a simple, actionable decision (e.g., "BUY", "SELL", "HOLD").
  * **Response Parsing:** Parse the JSON response from the Gemini API to extract the trading decision.

### **3.4. Trade Execution Simulator (`simulator.py`)**

  * **Continuous Monitoring:** This script will run in a separate thread or process. It will have a loop that executes every second.
  * **Price Checking:** In each iteration, it will:
    1.  Read the `ongoing_trades` and `current_prices` from `database.json`.
    2.  For each trade, it will check if the `current_price` of the pair has crossed the `stop_loss` or `take_profit` level.
  * **Trade Closure:** If a stop-loss or take-profit is hit:
    1.  The trade is removed from the `ongoing_trades` list.
    2.  The `account_balance` is updated based on the profit or loss from the trade.
    3.  A log of the closed trade is recorded.

-----

## **4. Workflow** 🔄

1.  **Initialization:**

      * The user starts the `main.py` and `simulator.py` scripts.
      * The `database.json` is initialized with a starting balance and empty trade list.

2.  **Scheduled Check (every 10 minutes):**

      * The `main.py` scheduler triggers the trading logic.
      * It checks if the number of ongoing trades is at its maximum (`x`).
          * If yes, it tries to close a profitable trade. If successful, it proceeds. Otherwise, it waits for the next cycle.
      * It prepares the latest chart data for analysis.

3.  **Decision Making:**

      * The chart data is sent to the Gemini API via `gemini_client.py`.
      * The Gemini API returns a decision: "BUY", "SELL", or "HOLD".

4.  **Trade Execution:**

      * If the decision is "BUY" or "SELL", a new trade is recorded in `database.json` with entry price, stop-loss, and take-profit levels.
      * The `account_balance` is not immediately affected upon opening a trade.

5.  **Continuous Simulation (every second):**

      * The `simulator.py` script reads the open trades and current prices.
      * It checks each trade to see if the current price has hit the stop-loss or take-profit.
      * If a condition is met, the trade is closed, profit/loss is calculated, and the `account_balance` in `database.json` is updated.

-----

## **5. Implementation Details** 💻

  * **Language:** **Python 3.x**

  * **Key Libraries:**

      * `schedule`: For scheduling the 10-minute trading checks.
      * `requests` or `google-generativeai`: For interacting with the Gemini API.
      * `json`: for reading and writing to the database file.
      * `threading` or `multiprocessing`: To run the `simulator.py` script concurrently with the main bot.

  * **Project Structure:**

    ```
    /crypto_trading_sim
    |-- main.py
    |-- simulator.py
    |-- gemini_client.py
    |-- database.json
    |-- config.py         # For API keys and other configurations
    |-- requirements.txt
    |-- README.md
    ```

-----

## **6. Future Enhancements** 🚀

  * **Live Data Integration:** Replace the local JSON price updates with a real-time data feed from a crypto exchange API.
  * **Advanced Trading Strategies:** Implement more complex strategies beyond simple scalping.
  * **Web Interface:** Create a simple web dashboard using Flask or Django to visualize the account balance, trade history, and ongoing trades.
  * **Historical Backtesting:** Develop a feature to test the trading strategy on historical price data to evaluate its performance.
  * **Persistent Database:** Replace the JSON file with a more robust database solution like SQLite or a time-series database for better performance and scalability.