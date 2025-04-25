import yfinance as yf
import pymongo
import pandas as pd
from datetime import datetime

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Veritabanı
db = client["DataSet"]

# Kurlar ve koleksiyonlar
currencies = {
    "EUR/TRY": {
        "ticker": "EURTRY=X",
        "collection": db["EUR/TRY"]
    },
    "USD/TRY": {
        "ticker": "USDTRY=X",
        "collection": db["USD/TRY"]
    }
}

# Tarih aralığı
date_range = pd.date_range(start=datetime(2025, 1, 1), end=datetime.now())

# Yardımcı fonksiyon: en yakın fiyatı bul
def get_latest_price(data, date, price_column='Close'):
    recent_data = data[data['Date'] <= date]
    if not recent_data.empty:
        return recent_data.iloc[-1][price_column]
    return None

# Her bir döviz kuru için veri çek ve yaz
for name, info in currencies.items():
    print(f"Fetching {name}...")

    ticker = yf.Ticker(info["ticker"])
    history = ticker.history(period="1y")

    if history.empty:
        print(f"No data found for {name}")
        continue

    history.reset_index(inplace=True)
    history['Date'] = history['Date'].dt.tz_localize(None)

    collection = info["collection"]
    latest_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])

    if latest_record and isinstance(latest_record['Date'], datetime):
        new_data = history[history['Date'] > latest_record['Date']]
    else:
        new_data = history

    if not new_data.empty:
        data_to_insert = []
        latest_day_record = collection.find_one(sort=[("Day", pymongo.DESCENDING)])
        starting_day = latest_day_record['Day'] + 1 if latest_day_record else 1

        for current_date in date_range:
            latest_price = get_latest_price(new_data, current_date)
            if latest_price is not None:
                data_to_insert.append({
                    'Date': current_date,
                    'Price': f"{latest_price:.2f} TL",
                    'Day': starting_day
                })
                starting_day += 1

        for record in data_to_insert:
            collection.insert_one(record)
            print(f"{name} -> {record['Date']} inserted")
    else:
        print(f"No new data for {name}")
