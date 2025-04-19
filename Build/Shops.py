import pymongo
import datetime

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

db = client["Final_Project"]


def get_last_inserted_date(collection):
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None


def db_shop(manufacturer_name, shop_name, profit_percentage):
    manufacturer_collection = db[manufacturer_name]
    shop_collection = db[shop_name]

    last_date_shop = get_last_inserted_date(shop_collection)

# Calculate for every data in manufacturer_name
    query = {}
    if last_date_shop:
        query = {'Date': {'$gt': last_date_shop}}

    # Calculate 3 months ago
    # three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)
    #
    # query = {'Date': {'$gte': three_months_ago}}

    cursor = manufacturer_collection.find(query)

    # Check if there are new records to process
    if manufacturer_collection.count_documents(query) == 0:
        print(f"No new data to insert for {shop_name}. Checking for updates to existing records...")
        query = {'Date': {'$lte': last_date_shop}}
        cursor = manufacturer_collection.find(query)

    for record in cursor:
        date = record['Date']

        shop_record = shop_collection.find_one({"Date": date}) or {
            "Date": date,
            "Profit Percentage": profit_percentage,
            "Store Type": shop_name,
            "Description": f"Product prices for {shop_name} as of {date}.",
        }

        product_group = f"{manufacturer_name} Products"
        if product_group not in shop_record:
            shop_record[product_group] = {}

        product_keys = [key for key in record.keys() if key.startswith("Product ")]
        product_counter = 1

        updated = False
        for key in product_keys:
            if "Price" in key:
                price = float(record[key].replace(" TL", "").replace(",", ""))
                new_price = price * (1 + profit_percentage / 100)

                # Check if the product or price has changed
                existing_product = shop_record[product_group].get(f"Product {product_counter}")
                existing_price = shop_record[product_group].get(f"Product {product_counter} Price")
                if (
                        existing_product != record[f"Product {product_counter}"]
                        or existing_price != f"{new_price:,.2f} TL"
                ):
                    updated = True

                shop_record[product_group][f"Product {product_counter}"] = record[f"Product {product_counter}"]
                shop_record[product_group][f"Product {product_counter} Price"] = f"{new_price:,.2f} TL"
                product_counter += 1

        if updated or not shop_collection.find_one({"Date": date}):
            new_shop_record = {
                "Date": shop_record["Date"],
                "Profit Percentage": shop_record["Profit Percentage"],
                "Store Type": shop_record["Store Type"],
                "Description": shop_record["Description"],
            }

            for key in sorted(shop_record.keys()):
                if key.endswith("Products"):
                    new_shop_record[key] = shop_record[key]

            existing_record = shop_collection.find_one({"Date": date})

            if existing_record:
                shop_collection.update_one({"_id": existing_record["_id"]}, {"$set": new_shop_record})
                print(f"Updated record for {shop_name} on {date}.")
            else:
                shop_collection.insert_one(new_shop_record)
                print(f"Inserted new record for {shop_name} on {date}.")
        else:
            print(f"No changes detected for {shop_name} on {date}. Record is up to date.")


db_shop("CableMan", "IKEA", 13)
db_shop("CableMan", "KablocuAhmet", 5)
db_shop("CableMan", "A101", 7)
db_shop("CableMan", "MIGROS", 10)
db_shop("ToyMan", "ToyzSHop", 10)
db_shop("CableMan", "ToyzSHop", 10)
db_shop("ELectronicMan", "MediaMarkt", 15)
db_shop("HomeELectricMan", "MediaMarkt", 15)
db_shop("ELectronicMan", "Teknosa", 10)
db_shop("HomeELectricMan", "Teknosa", 10)
db_shop("ELectronicMan", "Vatan", 7)
db_shop("HomeELectricMan", "Vatan", 7)
# db_shop("HomeELectricMan", "YourElectrician", 5)
# db_shop("HomeELectricMan", "MyElectrician", 5)
# db_shop("HomeELectricMan", "HisElectrician", 5)
