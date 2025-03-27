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


# delete_last_x_days("KablocuAhmet", 9)  # Deletes data from the last 5 days in the 'KablocuAhmet' collection
# delete_last_x_days("CableMan", 9)
# delete_last_x_days("CableMan2", 9)
# delete_last_x_days("CableMan3", 9)
# delete_last_x_days("ToyMan", 9)
# delete_last_x_days("ELectronicMan", 9)
# delete_last_x_days("HomeELectricMan", 9)
# delete_last_x_days("ELectricMan", 9)
delete_last_x_days("Gold/TRY", 20)
delete_last_x_days("Copper/TRY", 20)
delete_last_x_days("Aluminum/TRY", 20)
delete_last_x_days("Silver/TRY", 20)
delete_last_x_days("EUR/TRY", 20)
delete_last_x_days("USD/TRY", 20)

