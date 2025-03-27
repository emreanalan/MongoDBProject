import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

db = client["Final_Project"]

def get_last_inserted_date(collection):
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None

def db_distributor(distributor_name, db_manufacturer_name, profit_percentage):
    manufacturer_collection = db[db_manufacturer_name]
    distributor_collection = db[distributor_name]

    last_date = get_last_inserted_date(distributor_collection)
    query = {'Date': {'$gte': last_date}} if last_date else {}
    cursor = manufacturer_collection.find(query)

    if manufacturer_collection.count_documents(query) == 0:
        print(f"No new data to update for {distributor_name}. Database is up-to-date.")
        return

    for record in cursor:
        date = record['Date']
        distributor_record = {
            "Date": date,
            "Profit Percentage": profit_percentage,
            "Description": record["Description"],
        }

        product_keys = [key for key in record.keys() if key.startswith("Product ")]
        for key in product_keys:
            if "Price" in key:
                price = float(record[key].replace(" TL", "").replace(",", ""))
                new_price = price * (1 + profit_percentage / 100)
                distributor_record[key] = f"{new_price:,.2f} TL"
            else:
                distributor_record[key] = record[key]

        existing_record = distributor_collection.find_one({"Date": date})
        if existing_record:
            new_products = {k: v for k, v in distributor_record.items() if k not in existing_record}
            distributor_collection.update_one({"_id": existing_record["_id"]}, {"$set": new_products})
            print(f"Updated record for {distributor_name} on {date}: Added/updated products.")
        else:
            distributor_collection.insert_one(distributor_record)
            print(f"Inserted new record for {distributor_name} on {date}.")

    print(f"Finished updating {distributor_name}.")


db_distributor("CableStore", "CableMan", 10)
db_distributor("CableStore2", "CableMan2", 5)
db_distributor("CableStore3", "CableMan3", 15)
db_distributor("ToyStore", "ToyMan", 2)
db_distributor("ElectricMan", "ElectricDis", 5)
