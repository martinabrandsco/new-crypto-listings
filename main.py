import os
import requests
from datetime import datetime

# Get API keys from environment variables
API_KEY = os.getenv('COINMARKETCAP_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')

COINMARKETCAP_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
COIN_INFO_URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info'

# Set headers for API authentication
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': API_KEY,
}

def get_newly_listed_cryptos():
    # Define the start and end times for the current hour window
    now = datetime.utcnow()
    start_of_hour = now.replace(minute=0, second=0, microsecond=0)
    end_of_hour = start_of_hour + timedelta(hours=1)

    params = {
        'start': '1',  # start from the first currency
        'limit': '100',  # fetch 100 currencies at a time, adjust as needed
        'sort': 'date_added',  # Sort by listing date
    }

    try:
        response = requests.get(COINMARKETCAP_URL, headers=headers, params=params, timeout=10)  # Add a timeout

        if response.status_code == 200:
            data = response.json()['data']
            # Filter cryptocurrencies added within the last hour
            new_cryptos = [
                crypto for crypto in data if start_of_hour <= datetime.strptime(crypto['date_added'], '%Y-%m-%dT%H:%M:%S.%fZ') < end_of_hour
            ]
            print(f"Found {len(new_cryptos)} new cryptos listed in the last hour.")  # Debug log
            return new_cryptos
        else:
            print(f"Error fetching data from CoinMarketCap: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error during CoinMarketCap API request: {e}")
        return []


def get_token_contract_addresses(crypto_id):
    params = {
        'id': crypto_id
    }
    try:
        response = requests.get(COIN_INFO_URL, headers=headers, params=params, timeout=10)  # Add a timeout
        if response.status_code == 200:
            data = response.json()['data']
            return data[str(crypto_id)].get('contract_address', [])
        else:
            print(f"Error fetching contract address: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error during CoinMarketCap API request: {e}")
        return []


def send_telegram_message(message):
    telegram_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    params = {
        'chat_id': TELEGRAM_GROUP_ID,
        'text': message,
        'parse_mode': 'HTML'  # Optional: Allows you to format the text
    }
    try:
        response = requests.post(telegram_url, params=params, timeout=10)  # Add a timeout
        if response.status_code == 200:
            print("Message sent successfully.")  # Debug log
        else:
            print(f"Error sending message to Telegram: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error during Telegram API request: {e}")


new_cryptos = get_newly_listed_cryptos()

if new_cryptos:
    for crypto in new_cryptos:
        crypto_id = crypto['id']
        name = crypto['name']
        symbol = crypto['symbol']
        date_added = crypto['date_added']
        market_cap = crypto['quote']['USD'].get('market_cap', 'Not Available')

        contract_addresses = get_token_contract_addresses(crypto_id)

        message = f"<b>New Cryptocurrency Listed in the Last Hour</b>\n"
        message += f"Name: {name}\nSymbol: {symbol}\nDate Added: {date_added}\nMarket Cap: {market_cap}\n"

        if contract_addresses:
            for address in contract_addresses:
                message += f"Contract Address ({address['platform']['name']}): {address['contract_address']}\n"
        else:
            message += "No contract address available.\n"

        send_telegram_message(message)
else:
    send_telegram_message("No new cryptocurrencies listed in the last hour.")
