import pymongo
from datetime import datetime, timedelta

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]


def get_previous_profit(shop_collection, previous_date):
    previous_record = shop_collection.find_one({"Date": previous_date})
    return previous_record["Profit Percentage"] if previous_record else None


def db_shop_with_cheater_interval(manufacturer_name, shop_name, start_date_str, end_date_str, extra_profit_percentage,
                                  cheater_product=None):
    manufacturer_collection = db[manufacturer_name]
    shop_collection = db[shop_name]

    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)
    previous_day = start_date - timedelta(days=1)

    base_profit = get_previous_profit(shop_collection, previous_day)
    if base_profit is None:
        print("No previous record found to base the cheater profit on.")
        return

    adjusted_profit = base_profit + extra_profit_percentage

    current_date = start_date
    while current_date <= end_date:
        manufacturer_record = manufacturer_collection.find_one({"Date": current_date})
        if not manufacturer_record:
            current_date += timedelta(days=1)
            continue

        shop_record = {
            "Date": current_date,
            "Profit Percentage": adjusted_profit,
            "Store Type": shop_name,
            "Description": f"Product prices for {shop_name} as of {current_date.date()}"
        }

        product_group = f"{manufacturer_name} Products"
        shop_record[product_group] = {}

        product_keys = [key for key in manufacturer_record if key.startswith("Product ")]
        product_counter = 1

        for key in product_keys:
            if "Price" in key:
                price = float(manufacturer_record[key].replace(" TL", "").replace(",", ""))
                new_price = price * (1 + adjusted_profit / 100)

                if cheater_product is None or f"Product {product_counter}" == cheater_product:
                    shop_record[product_group][f"Product {product_counter}"] = manufacturer_record[
                        f"Product {product_counter}"]
                    shop_record[product_group][f"Product {product_counter} Price"] = f"{new_price:,.2f} TL"

                product_counter += 1

        db[shop_name].insert_one(shop_record)
        print(f"Inserted cheater record for {shop_name} on {current_date.date()} with {adjusted_profit}% profit")

        current_date += timedelta(days=1)

# Örnek kullanım:
db_shop_with_cheater_interval("CableMan", "IKEA", "2025-03-20", "2025-03-25", 3)