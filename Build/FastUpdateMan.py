import pymongo
import random

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

db = client["DataSet"]
profit_percentage = random.randint(2, 12)
def get_last_inserted_date(collection):
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None

def db_manufacturer(manufacturer_name, profit_percentage, *product_names):
    manufacturer_collection = db[manufacturer_name]

    # Get the last inserted date in the manufacturer's collection
    last_date_manufacturer = get_last_inserted_date(manufacturer_collection)

    # Build a query for products newer than the last inserted date
    query = {}
    if last_date_manufacturer:
        query = {"Date": {"$gte": last_date_manufacturer}}

    # Iterate through all product collections
    for product_name in product_names:
        product_collection = db[product_name]
        cursor = product_collection.find(query, {"Date": 1, "Cost": 1}).sort("Date", pymongo.ASCENDING)

        for record in cursor:
            date = record['Date']
            cost = record['Cost']

            new_price = float(cost.replace(" TL", "").replace(",", "")) * (1 + profit_percentage / 100)
            new_price_str = f"{new_price:,.2f} TL"

            # Check for an existing record on the same date
            existing_record = manufacturer_collection.find_one({"Date": date})

            if existing_record:
                # Check if the product already exists in the record
                product_exists = any(
                    existing_record.get(f"Product {i}") == product_name
                    for i in range(1, len(existing_record) + 1)
                    if f"Product {i}" in existing_record
                )

                if not product_exists:
                    # Add the new product to the record
                    num_products = len(
                        [key for key in existing_record.keys() if key.startswith("Product") and "Price" not in key]
                    )
                    new_product_index = num_products + 1

                    update_fields = {
                        f"Product {new_product_index}": product_name,
                        f"Product {new_product_index} Price": new_price_str,
                    }

                    updated_description = f"{existing_record['Description']} and {product_name}"
                    update_fields["Description"] = updated_description

                    manufacturer_collection.update_one({"_id": existing_record["_id"]}, {"$set": update_fields})
                    print(f"Updated record for date {date}: Added {product_name}.")
                else:
                    print(f"Product {product_name} already exists for date {date}.")
            else:
                # Insert a new record for the date
                new_record = {
                    "Date": date,
                    "Description": product_name,
                    "Profit Percentage": profit_percentage,
                    "Product 1": product_name,
                    "Product 1 Price": new_price_str
                }
                manufacturer_collection.insert_one(new_record)
                print(f"Inserted new record for date {date}: Added {product_name}.")

    print(f"All products processed for manufacturer {manufacturer_name}.")

def manufacturerProductionRate(manufacturer_name, production_rate, *product_names):
    profit_percentage = {
        "low": 10,
        "moderate": 7,
        "high": 5
    }.get(production_rate.lower())

    if profit_percentage is None:
        print(f"Invalid production rate: {production_rate}. Use 'low', 'moderate', or 'high'.")
        return

    db_manufacturer(manufacturer_name, profit_percentage, *product_names)
#db_manufacturer("CableMan", "low", "CopperCable 1m", "GoldCable 1m", "USBCable", "SilverCable 1m")

# db_manufacturer("CableMan", 15, "CopperCable 1m", "GoldCable 1m", "USBCable", "SilverCable 1m")
# db_manufacturer("CableMan2", 10, "CopperCable 1m", "GoldCable 1m", "USBCable", "SilverCable 1m")
# db_manufacturer("CableMan3", 20, "CopperCable 1m", "GoldCable 1m", "USBCable", "SilverCable 1m")
# db_manufacturer("ToyMan", 10, "Toy_Car", "Toy_AliminumGun", "Toy_TeddyBear", "GamePad")
# db_manufacturer("ELectronicMan", 15, "Laptop", "Smartphone", "Tablet", "Smart Watch", "Gaming Mouse", "Television", "Camera")
# db_manufacturer("HomeELectricMan", 10, "Electric Fan", "Microwave", "Vacuum Cleaner", "Air Conditioner", "Refrigerator", "Electric Kettle", "Blender")
# db_manufacturer("ELectricMan", 15, "Printer")

all_products = [f"Product {i}" for i in range(1, 501)]

for i in range(25):
    manufacturer_name = f"Man{i+1}"
    assigned_products = all_products[i*20 : (i+1)*20]
    profit_percentage = random.randint(2, 12)
    db_manufacturer(manufacturer_name, profit_percentage, *assigned_products)
