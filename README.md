# Crypto Price Alert Bot

This repository contains a Telegram bot for tracking cryptocurrency prices and setting up price alerts. The bot uses the CoinGecko API to fetch cryptocurrency prices and the `python-telegram-bot` library to interact with Telegram users.

## Features

- Get the current price of a specified cryptocurrency.
- Set up price alerts for specific conditions (e.g., when the price goes above or below a target value).
- View and manage active price alerts.
- Caching of coin mappings to reduce API calls.
- Periodic checking of price alerts.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/crypto-price-alert-bot.git
    cd crypto-price-alert-bot
    ```

2. Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your Telegram bot token:
    ```env
    TELEGRAM_API_TOKEN=your_telegram_bot_token
    ```

## Usage

1. Run the bot:
    ```bash
    python price_alert_bot.py
    ```

2. Interact with the bot on Telegram using the following commands:
    - `/start`: Start the bot and get a welcome message.
    - `/price <crypto> <currency>`: Get the current price of the specified cryptocurrency.
    - `/alert <crypto> <condition> <target_price> <currency>`: Set up a price alert.
    - `/alerts`: View active price alerts.
    - `/del <alert_id>`: Delete a specific price alert.

## Example Commands

- `/price BTC USD`: Get the current price of Bitcoin in USD.
- `/alert BTC above 50000 USD`: Set an alert for when Bitcoin's price goes above 50,000 USD.
- `/alerts`: View your active price alerts.
- `/del 1`: Delete the alert with ID 1.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.