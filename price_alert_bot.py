import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import uuid
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cache for coin mappings
coin_map_cache: Dict[str, str] = {}

# Dictionary to store price alerts
price_alerts: Dict[int, list] = {}

# Maximum number of alerts per user
MAX_ALERTS_PER_USER = 5


def get_coin_id(ticker: str) -> Optional[str]:
    """Get CoinGecko ID from ticker symbol"""
    ticker = ticker.lower()

    # Check cache first
    if ticker in coin_map_cache:
        return coin_map_cache[ticker]

    try:
        # Get coin list from CoinGecko
        url = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url)
        response.raise_for_status()
        coins = response.json()

        # Find coin by ticker
        for coin in coins:
            if coin["symbol"] == ticker:
                coin_map_cache[ticker] = coin["id"]
                return coin["id"]
        return None
    except Exception as e:
        logger.error(f"Error getting coin ID: {e}")
        return None


def get_ticker_price(coin_id: str, target: str = "USDT") -> Optional[float]:
    """Get crypto price from tickers endpoint"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/tickers"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Find USDT pair from Binance preferably
        for ticker in data["tickers"]:
            if (
                ticker["target"] == target
                and ticker["market"]["identifier"] == "binance"
            ):
                return ticker["last"]

        # Fallback to first USDT pair
        for ticker in data["tickers"]:
            if ticker["target"] == target:
                return ticker["last"]

        return None
    except Exception as e:
        logger.error(f"Error fetching ticker price: {e}")
        return None


def get_crypto_price(ticker: str, currency: str = "usdt") -> Optional[float]:
    """Get crypto price using ticker"""
    try:
        coin_id = get_coin_id(ticker.lower())
        if not coin_id:
            return None

        price = get_ticker_price(coin_id, currency.upper())
        if price:
            return price

        # Fallback to simple price endpoint
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data[coin_id][currency]
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return None


# Command handler: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Crypto Price Tracker Bot! Use /price <crypto> <currency> to get the price."
    )


# Command handler: Price
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /price <crypto> <currency>")
        return

    ticker = context.args[0]
    currency = context.args[1] if len(context.args) > 1 else "usdt"
    price = get_crypto_price(ticker, currency)

    if price:
        await update.message.reply_text(
            f"The price of {ticker.upper()} in {currency.upper()} is {price}"
        )
    else:
        await update.message.reply_text(
            f"Could not fetch the price for {ticker.upper()} in {currency.upper()}"
        )


async def set_alert(update, context):
    user_id = update.effective_user.id

    # Check if user has reached max alerts
    if user_id in price_alerts and len(price_alerts[user_id]) >= MAX_ALERTS_PER_USER:
        await update.message.reply_text(
            f"You've reached the maximum limit of {MAX_ALERTS_PER_USER} alerts. "
            "Delete some alerts using /delalert before adding new ones."
        )
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: /setalert <crypto> <target_price> <above/below> [currency]"
        )
        return

    try:
        crypto = context.args[0].lower()
        target_price = float(context.args[1])
        condition = context.args[2].lower()
        currency = context.args[3].lower() if len(context.args) > 3 else "usd"

        if condition not in ["above", "below"]:
            await update.message.reply_text("Condition must be 'above' or 'below'")
            return

        alert = {
            "id": str(uuid.uuid4())[:8],  # Short unique ID
            "crypto": crypto,
            "currency": currency,
            "target_price": target_price,
            "condition": condition,
        }

        if user_id not in price_alerts:
            price_alerts[user_id] = []
        price_alerts[user_id].append(alert)

        await update.message.reply_text(
            f"Alert #{alert['id']} set for {crypto.upper()} "
            f"when price is {condition} {target_price} {currency.upper()}"
        )
    except ValueError:
        await update.message.reply_text("Invalid price value. Please enter a number.")


async def del_alert(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /delalert <alert_id>")
        return

    user_id = update.effective_user.id
    alert_id = context.args[0]

    if user_id not in price_alerts:
        await update.message.reply_text("You have no active alerts.")
        return

    for alert in price_alerts[user_id][:]:
        if alert["id"] == alert_id:
            price_alerts[user_id].remove(alert)
            await update.message.reply_text(f"Alert #{alert_id} deleted.")
            return

    await update.message.reply_text(f"Alert #{alert_id} not found.")


async def check_alerts(context):
    for user_id, alerts in price_alerts.items():
        for alert in alerts[:]:  # Create a copy to allow removal during iteration
            crypto = alert["crypto"]
            currency = alert["currency"]
            current_price = get_crypto_price(crypto, currency)

            if current_price:
                condition_met = (
                    alert["condition"] == "above"
                    and current_price > alert["target_price"]
                ) or (
                    alert["condition"] == "below"
                    and current_price < alert["target_price"]
                )

                if condition_met:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 Alert: {crypto.upper()} is now {alert['condition']} {alert['target_price']} {currency.upper()}!\n"
                        f"Current price: {current_price} {currency.upper()}",
                    )
                    # Remove the alert once triggered
                    price_alerts[user_id].remove(alert)


async def my_alerts(update, context):
    user_id = update.effective_user.id
    if user_id not in price_alerts or not price_alerts[user_id]:
        await update.message.reply_text("You have no active alerts.")
        return

    alert_messages = []
    for alert in price_alerts[user_id]:
        alert_messages.append(
            f"#{alert['id']}: {alert['crypto'].upper()} {alert['condition']} "
            f"{alert['target_price']} {alert['currency'].upper()}"
        )

    await update.message.reply_text(
        f"Your active alerts ({len(alert_messages)}/{MAX_ALERTS_PER_USER}):\n"
        + "\n".join(alert_messages)
        + "\n\nUse /delalert <alert_id> to remove an alert."
    )


def register_handlers(application: Application) -> None:
    """Register command handlers with the application"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("alert", set_alert))
    application.add_handler(CommandHandler("alerts", my_alerts))
    application.add_handler(CommandHandler("del", del_alert))


def setup_jobs(application: Application) -> None:
    """Setup job queue for periodic tasks"""
    job_queue = application.job_queue
    job_queue.run_repeating(check_alerts, interval=60 * 5)


def main():
    api_token = os.getenv("TELEGRAM_TOKEN")
    if not api_token:
        print("Error: TELEGRAM_API_TOKEN environment variable is not set.")
        return

    application = Application.builder().token(api_token).build()

    # Register handlers and setup jobs
    register_handlers(application)
    setup_jobs(application)

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
