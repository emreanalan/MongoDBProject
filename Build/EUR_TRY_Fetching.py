import yfinance as yf
import pymongo
import pandas as pd
from datetime import datetime

# Step 1: Connect to MongoDB Atlas
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Step 2: Select your database and collection
db = client["Final_Project"]
collection = db["EUR/TRY"]

# Step 3: Fetch the EUR/TRY exchange rate data for the past year
eur_try = yf.Ticker("EURTRY=X")
eur_try_history = eur_try.history(period="1y")

# Step 4: Reset index and extract the 'Date' and 'Close' columns
eur_try_history.reset_index(inplace=True)

# Step 5: Ensure 'Date' in eur_try_history is tz-naive for comparison
eur_try_history['Date'] = eur_try_history['Date'].dt.tz_localize(None)


# Step 6: Define the function to fetch the latest available price for a given date
def get_latest_price(data, date, price_column='Close'):
    """Fetches the latest available price for a given date from the provided data."""
    # Find the most recent date that is less than or equal to the target date
    recent_data = data[data['Date'] <= date]
    if not recent_data.empty:
        return recent_data.iloc[-1][price_column]
    return None


# Step 7: Check for the latest 'Date' in the MongoDB collection
latest_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])

if latest_record:
    latest_date = latest_record['Date']
    if isinstance(latest_date, datetime):
        # Filter the eur_try_history DataFrame to include only new dates
        new_data = eur_try_history[eur_try_history['Date'] > latest_date]
    else:
        raise TypeError(f"Expected 'Date' from MongoDB to be datetime, got {type(latest_date)}")
else:
    # If no records exist, insert everything
    new_data = eur_try_history

# Step 8: Generate a complete date range for the last year
date_range = pd.date_range(start=datetime.now() - pd.DateOffset(years=1), end=datetime.now())

# Step 9: Prepare the new data, filling missing dates with the last available price
if not new_data.empty:
    data_to_insert = []
    latest_day_record = collection.find_one(sort=[("Day", pymongo.DESCENDING)])
    starting_day = latest_day_record['Day'] + 1 if latest_day_record else 1

    for current_date in date_range:
        # Get the latest price for the current date, even if no new data exists
        latest_price = get_latest_price(new_data, current_date)

        if latest_price is not None:
            data_to_insert.append({
                'Date': current_date,
                'Price': f"{latest_price:.2f} TL",
                'Day': starting_day,
            })
            starting_day += 1

    if data_to_insert:
        for record in data_to_insert:
            collection.insert_one(record)
            print(f"Record inserted into MongoDB: Date: {record['Date']}, Price: {record['Price']}, Day: {record['Day']}")
    else:
        print("No data to insert. The database is up to date.")
else:
    print("No new data to insert. The database is already up to date.")
