import pymongo

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

db = client["Final_Project"]

def get_last_inserted_date(collection):
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None

def db_shop_with_cheater(manufacturer_name, shop_name, profit_percentage, is_cheater=False, cheater_product=None):
    manufacturer_collection = db[manufacturer_name]
    shop_collection = db[shop_name]

    last_date_shop = get_last_inserted_date(shop_collection)

    last_date_manufacturer = get_last_inserted_date(manufacturer_collection)

    query = {}
    if last_date_shop:
        query = {'Date': {'$gt': last_date_shop}}

    cursor = manufacturer_collection.find(query)

    if manufacturer_collection.count_documents(query) == 0:
        print(f"No new data to insert for {shop_name}. Record is up to date.")
        return

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

        if is_cheater:
            if cheater_product is None or f"Product {product_counter}" == cheater_product:
                extra_profit_percentage = float(
                    input(
                        f"Enter extra profit percentage for {f'Product {product_counter}' if cheater_product else 'all products'}: ")
                )
                adjusted_profit_percentage = profit_percentage + extra_profit_percentage
            else:
                adjusted_profit_percentage = profit_percentage
        else:
            adjusted_profit_percentage = profit_percentage

        for key in product_keys:
            if "Price" in key:
                # Extract price
                price = float(record[key].replace(" TL", "").replace(",", ""))


                new_price = price * (1 + adjusted_profit_percentage / 100)

                shop_record[product_group][f"Product {product_counter}"] = record[f"Product {product_counter}"]
                shop_record[product_group][f"Product {product_counter} Price"] = f"{new_price:,.2f} TL"
                product_counter += 1

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
            new_products = {k: v for k, v in new_shop_record.items() if k not in existing_record}
            shop_collection.update_one({"_id": existing_record["_id"]}, {"$set": new_products})
            print(f"Updated record for {shop_name} on {date}: Added new products.")
        else:
            # Insert the new record
            shop_collection.insert_one(new_shop_record)
            print(f"Inserted new record for {shop_name} on {date}.")


db_shop_with_cheater("CableMan", "KablocuAhmet", 5, is_cheater=True, cheater_product="Product 1")
db_shop_with_cheater("CableMan", "KablocuAhmet", 5, is_cheater=True)
