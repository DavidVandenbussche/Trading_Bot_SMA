# Crypto Trading Bot

## Overview
This bot is designed to automate trading strategies on the Phemex cryptocurrency exchange platform. Utilizing technical analysis and market orders, the bot makes decisions based on simple moving averages (SMAs) over daily and 15-minute intervals to execute buy or sell orders. It aims to capitalize on market trends by dynamically adjusting its positions based on real-time market data.

## Features
- **Automatic Order Execution**: Places limit buy/sell orders based on predefined strategies involving SMAs.
- **Position Management**: Manages open positions, adjusting orders to mitigate risk and secure profits.
- **Kill Switch**: A safety feature to close all positions in case of unexpected market movements or when specific profit targets are met.
- **Continuous Monitoring**: Runs trading strategies periodically, reassessing market conditions and adjusting orders accordingly.

## Dependencies
To run this bot, you'll need Python 3.x and the following packages:
- `ccxt`: For connecting to the Phemex exchange API.
- `pandas`: For data manipulation and analysis.
- `schedule`: For running the trading function at regular intervals.
- `requests`: For making HTTP requests (not directly used in the provided script but included in imports).
- `time`: For managing delays and scheduling tasks.

Additionally, a configuration file (`dontshareconfig.py`) is required for storing sensitive API keys securely.

## Setup
1. **Install Dependencies**: Ensure Python 3.x is installed, then install required packages using pip: pip install ccxt pandas schedule requests
pip install ccxt pandas schedule requests
2. **API Keys**: To use the bot, you need to obtain your API Key and Secret from Phemex. Once you have them, update the `dontshareconfig.py` file with your credentials:

```python
API_KEY = 'your_api_key'
SECRET_KEY = 'your_secret_key'
```

## Safety and Compliance
- **Rate Limits Compliance**: The bot adheres to the Phemex API's rate limits to ensure safe and compliant operation.
- **Sandbox Testing**: Before live trading, it's recommended to test the bot in a sandbox environment. This can be done by uncommenting `phemex.set_sandbox_mode(True)` in the script.
- **Understanding Risks**: Ensure you have a comprehensive understanding of the trading strategies employed by the bot and are fully aware of the risks associated with automated trading.

## Disclaimer
This bot is provided "as-is" for educational purposes only and comes without any guarantee of profitability. The creator will not be held responsible for any financial losses incurred from its use. It is imperative to conduct thorough research and assess your risk tolerance before engaging in live trading.

