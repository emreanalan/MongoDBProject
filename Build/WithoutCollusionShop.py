from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB Client
client = MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

db = client["Final_Project"]

def without_collusion(mode, start_date, end_date, profit_percentage, *shops):
    if mode not in ("max", "min", "average"):
        print("Invalid mode. Please use 'max', 'min', or 'average'.")
        return

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    current_date = start_dt

    while current_date <= end_dt:
        # Collect product prices from all shops for the current date
        daily_prices = {}
        for shop in shops:
            record = db[shop].find_one({"Date": current_date})
            if record:
                for key, value in record.items():
                    if "Price" in key:
                        product_name = key.replace(" Price", "")
                        price = float(value.replace(" TL", "").replace(",", ""))
                        if product_name not in daily_prices:
                            daily_prices[product_name] = []
                        daily_prices[product_name].append(price)

        # Determine the new price for each product based on the mode
        calculated_prices = {}
        for product, prices in daily_prices.items():
            if mode == "max":
                calculated_price = max(prices)
            elif mode == "min":
                calculated_price = min(prices)
            elif mode == "average":
                calculated_price = sum(prices) / len(prices)

            # Apply profit percentage
            calculated_price *= (1 + profit_percentage / 100)
            calculated_prices[product] = f"{calculated_price:,.2f} TL"

        # Store the calculated prices in a new collection
        without_collusion_collection = db["WithoutCollusion"]
        new_record = {
            "Date": current_date,
            "Mode": mode,
            "Profit Percentage": profit_percentage,
            "Description": f"Calculated prices for shops {', '.join(shops)} on {current_date} using {mode} mode.",
            "Products": calculated_prices,
        }

        existing_record = without_collusion_collection.find_one({"Date": current_date, "Mode": mode})
        if existing_record:
            without_collusion_collection.update_one(
                {"_id": existing_record["_id"]}, {"$set": new_record}
            )
            print(f"Updated record for {current_date} with {mode} mode.")
        else:
            without_collusion_collection.insert_one(new_record)
            print(f"Inserted new record for {current_date} with {mode} mode.")

        current_date += timedelta(days=1)

without_collusion(
    "max",
    "2024-12-02T00:00:00.000+00:00",
    "2024-12-09T00:00:00.000+00:00",
    3,
    "MediaMarkt", "Teknosa", "Vatan"
)
