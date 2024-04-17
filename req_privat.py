import sys
from datetime import datetime, timedelta
import json
import asyncio

import aiohttp

class HttpError(Exception):
    pass

async def request(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise HttpError(f"Error status: {response.status} for {url}")

async def get_exchange_rate(date: str):
    url = f"https://api.privatbank.ua/p24api/exchange_rates?date={date}"
    try:
        data = await request(url)
        exchange_rate = {}
        for rate in data["exchangeRate"]:
            if rate["currency"] in ["EUR", "USD"]:
                exchange_rate[rate["currency"]] = {
                    "sale": rate["saleRateNB"],
                    "purchase": rate["purchaseRateNB"]
                }
        return exchange_rate
    except HttpError as e:
        print(f"Error fetching exchange rate for {date}: {e}")
        return None

async def count_date(index_days: int):
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%d.%m.%Y") for i in range(index_days)]
    exchange_rates = []
    for date in dates:
        exchange_rate = await get_exchange_rate(date)
        if exchange_rate:
            exchange_rates.append({date: exchange_rate})
    return exchange_rates

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <index_days>")
        sys.exit(1)
    try:
        index_days = int(sys.argv[1])
        if index_days > 10:
            print("Error: Index days cannot be greater than 10.")
            sys.exit(1)
    except ValueError:
        print("Error: Index days must be an integer.")
        sys.exit(1)

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(count_date(index_days))
    print(json.dumps(result, indent=2))
