import yfinance as yf
import pymongo
import pandas as pd
from datetime import datetime

# Step 1: Connect to MongoDB Atlas
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Step 2: Select your database and collection for each commodity
db = client["Final_Project"]

collections = {
    "Gold": db["Gold/TRY"],
    "Copper": db["Copper/TRY"],
    "Aluminum": db["Aluminum/TRY"],
    "Silver": db["Silver/TRY"]
}

# Commodity Tickers
tickers = {
    "Gold": "GC=F",      # Gold (Global prices in USD per ounce)
    "Copper": "HG=F",    # Copper (Global prices in USD per pound)
    "Aluminum": "ALI=F", # Aluminum (Global prices in USD per ton)
    "Silver": "SI=F"     # Silver (Global prices in USD per ounce)
}

# Step 3: Fetch the current USD/TRY exchange rate
def fetch_usd_to_try():
    usd_try = yf.Ticker("TRY=X")
    usd_try_history = usd_try.history(period="1d")
    return usd_try_history['Close'].iloc[0] if not usd_try_history.empty else None

# Step 4: Define the function to fetch the latest available price for a given date
def get_latest_price(data, date, price_column='Close'):
    """Fetches the latest available price for a given date from the provided data."""
    # Find the most recent date that is less than or equal to the target date
    recent_data = data[data['Date'] <= date]
    if not recent_data.empty:
        return recent_data.iloc[-1][price_column]
    return None

# Step 5: Fetch and insert data into MongoDB with price converted to TRY
def fetch_and_insert_data(commodity, ticker, usd_to_try):
    try:
        # Fetch historical data from Yahoo Finance
        commodity_data = yf.Ticker(ticker)
        commodity_history = commodity_data.history(period="1y")

        if commodity_history.empty:
            print(f"No data found for {commodity} ({ticker}).")
            return

        # Reset index to make 'Date' a column
        commodity_history.reset_index(inplace=True)
        commodity_history['Date'] = pd.to_datetime(commodity_history['Date'], utc=True).dt.tz_localize(None)

        # Get the collection for this commodity
        collection = collections[commodity]

        # Check for the latest 'Date' in the MongoDB collection
        latest_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])

        if latest_record:
            latest_date = latest_record['Date']
            new_data = commodity_history[commodity_history['Date'] > latest_date]
        else:
            new_data = commodity_history  # No records in DB, insert everything

        # Step 6: Generate a complete date range for the last year
        date_range = pd.date_range(start=datetime.now() - pd.DateOffset(years=1), end=datetime.now())

        # Step 7: Prepare the new data, filling missing dates with the last available price
        if not new_data.empty:
            data_to_insert = []
            latest_day_record = collection.find_one(sort=[("Day", pymongo.DESCENDING)])
            starting_day = latest_day_record['Day'] + 1 if latest_day_record else 1

            for current_date in date_range:
                latest_price = get_latest_price(new_data, current_date)

                if latest_price is not None:
                    record = {
                        'Date': current_date,
                        'Day': starting_day,
                    }

                    # Convert the price to TRY for the respective commodity
                    if commodity == "Gold":
                        record['Price'] = f"{(latest_price * 32.1507 * usd_to_try):,.2f} TL"
                    elif commodity == "Copper":
                        record['Price'] = f"{(latest_price / 0.453592 * usd_to_try):,.2f} TL"
                    elif commodity == "Silver":
                        record['Price'] = f"{(latest_price * 32.1507 * usd_to_try):,.2f} TL"
                    else:
                        record['Price'] = f"{(latest_price / 1000 * usd_to_try):,.2f} TL"

                    # Incremental 'Day' for each record
                    data_to_insert.append(record)
                    starting_day += 1

            if data_to_insert:
                for record in data_to_insert:
                    collection.insert_one(record)
                    print(f"Inserted into MongoDB: Date: {record['Date']}, Price: {record['Price']}, Day: {record['Day']}")
            else:
                print(f"No new data for {commodity}. The database is already up to date.")
        else:
            print(f"No new {commodity} data to insert. The database is already up to date.")

    except Exception as e:
        print(f"Error fetching data for {commodity}: {e}")

# Step 8: Fetch and insert data for each commodity
usd_to_try = fetch_usd_to_try()

if usd_to_try:
    for commodity, ticker in tickers.items():
        fetch_and_insert_data(commodity, ticker, usd_to_try)
else:
    print("Failed to fetch USD/TRY exchange rate. Please try again later.")
