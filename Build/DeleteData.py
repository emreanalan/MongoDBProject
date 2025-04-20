import pymongo
from datetime import datetime, timedelta

# MongoDB connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]


def delete_last_x_days(collection_name, days):
    collection = db[collection_name]

    cutoff_date = datetime.now() - timedelta(days=days)

    result = collection.delete_many({"Date": {"$gte": cutoff_date}})

    print(
        f"Deleted {result.deleted_count} records from '{collection_name}' that were inserted in the last {days} days.")


def delete_date_range(collection_name, start_date_str, end_date_str):
    collection = db[collection_name]
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    result = collection.delete_many({"Date": {"$gte": start_date, "$lte": end_date}})
    print(f"Deleted {result.deleted_count} records from '{collection_name}' between {start_date.date()} and {end_date.date()}.")

#delete_last_x_days("Copper/TRY", 20)
#delete_last_x_days("Aluminum/TRY", 20)
#delete_last_x_days("Silver/TRY", 20)
#delete_last_x_days("EUR/TRY", 20)
#delete_last_x_days("USD/TRY", 20)
#delete_last_x_days("Gold/TRY", 20)
# delete_date_range("IKEA", "2025-01-01", "2025-04-20")
# delete_date_range("A101", "2025-01-01", "2025-04-20")
# delete_date_range("MIGROS", "2025-01-01", "2025-04-20")
# delete_date_range("MediaMarkt", "2025-01-01", "2025-04-20")
# delete_date_range("Teknosa", "2025-01-01", "2025-04-20")
# delete_date_range("ToyMan", "2025-01-01", "2025-04-20")
# delete_date_range("KablocuAhmet", "2025-01-01", "2025-04-20")
# delete_date_range("ToyzSHop", "2025-01-01", "2025-04-20")
# delete_date_range("Vatan", "2025-01-01", "2025-04-20")
delete_date_range("MyElectrician", "2025-01-01", "2025-04-20")
delete_date_range("YourElectrician", "2025-01-01", "2025-04-20")
delete_date_range("HisElectrician", "2025-01-01", "2025-04-20")




