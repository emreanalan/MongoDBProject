import pymongo


client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")


db = client["Final_Project"]


def get_last_inserted_date(collection):
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None


def db_manufacturer(manufacturer_name, product_name, profit_percentage):
    manufacturer_collection = db[manufacturer_name]
    product_collection = db[product_name]


    cursor = product_collection.find({}, {'Date': 1, 'Cost': 1})

    for record in cursor:
        date = record['Date']
        cost = record['Cost']

        new_price = float(cost.replace(" TL", "").replace(",", "")) * (1 + profit_percentage / 100)
        new_price_str = f"{new_price:,.2f} TL"

        existing_record = manufacturer_collection.find_one({"Date": date})

        if existing_record:

            product_exists = any(
                existing_record.get(f"Product {i}") == product_name
                for i in range(1, len(existing_record) + 1)
                if f"Product {i}" in existing_record
            )

            if not product_exists:

                num_products = len(
                    [key for key in existing_record.keys() if key.startswith("Product") and "Price" not in key])
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
            new_record = {
                "Date": date,
                "Description": product_name,
                "Profit Percentage": profit_percentage,
                "Product 1": product_name,
                "Product 1 Price": new_price_str
            }
            manufacturer_collection.insert_one(new_record)
            print(f"Inserted new record for date {date}: Added {product_name}.")


db_manufacturer("CableMan", "CopperCable 1m", 15)
db_manufacturer("CableMan", "GoldCable 1m", 15)
db_manufacturer("CableMan", "USBCable", 15)
db_manufacturer("CableMan", "SilverCable 1m", 15)
db_manufacturer("CableMan2", "CopperCable 1m", 10)
db_manufacturer("CableMan2", "GoldCable 1m", 10)
db_manufacturer("CableMan2", "USBCable", 10)
db_manufacturer("CableMan2", "SilverCable 1m", 10)
db_manufacturer("CableMan3", "CopperCable 1m", 20)
db_manufacturer("CableMan3", "GoldCable 1m", 20)
db_manufacturer("CableMan3", "USBCable", 20)
db_manufacturer("CableMan3", "SilverCable 1m", 20)
db_manufacturer("ToyMan", "Toy_Car", 10)
db_manufacturer("ToyMan", "Toy_AliminumGun", 10)
db_manufacturer("ToyMan", "Toy_TeddyBear", 10)
db_manufacturer("ToyMan", "GamePad", 10)
db_manufacturer("ELectronicMan", "Laptop", 15)
db_manufacturer("ELectronicMan", "Smartphone", 15)
db_manufacturer("ELectronicMan", "Tablet", 15)
db_manufacturer("ELectronicMan", "Smart Watch", 15)
db_manufacturer("ELectronicMan", "Gaming Mouse", 15)
db_manufacturer("HomeELectricMan", "Electric Fan", 10)
db_manufacturer("HomeELectricMan", "Microwave", 10)
db_manufacturer("HomeELectricMan", "Vacuum Cleaner", 10)
db_manufacturer("HomeELectricMan", "Air Conditioner", 10)
db_manufacturer("ELectronicMan", "Television", 15)
db_manufacturer("HomeELectricMan", "Refrigerator", 10)
db_manufacturer("ELectricMan", "Printer", 15)
db_manufacturer("ELectronicMan", "Camera", 15)
db_manufacturer("HomeELectricMan", "Electric Kettle", 10)
db_manufacturer("HomeELectricMan", "Blender", 10)
