import pymongo
from datetime import datetime, timedelta

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]

products_collection = db["Products"]

product_list = [
    "CopperCable 1m",
    "GoldCable 1m",
    "USBCable",
    "SilverCable 1m",
    "Toy_Car",
    "Toy_AliminumGun",
    "Toy_TeddyBear",
    "GamePad",
    "Laptop",
    "Smartphone",
    "Tablet",
    "Smart Watch",
    "Gaming Mouse",
    "Electric Fan",
    "Microwave",
    "Vacuum Cleaner",
    "Air Conditioner",
    "Television",
    "Refrigerator",
    "Printer",
    "Camera",
    "Electric Kettle",
    "Blender"
]

# Set the date range
start_date = datetime(2025, 3, 1)
end_date = datetime(2025, 3, 26)
current_date = start_date

while current_date <= end_date:
    day_record = {
        "Date": current_date,
        "Description": "Product prices"
    }

    counter = 1
    for product in product_list:
        product_collection = db[product]
        product_data = product_collection.find_one({"Date": current_date})
        if product_data:
            day_record[f"Product {counter}"] = product
            day_record[f"Product {counter} Price"] = product_data["Cost"]
            counter += 1

    if counter > 1:
        products_collection.insert_one(day_record)
        print(f"Inserted record for {current_date.date()}")

    current_date += timedelta(days=1)
