import pymongo
from datetime import datetime, timedelta

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]

REFERENCE_COLLECTION = "Products"
TOTAL_THRESHOLD_PERCENTAGE = 32.5
MANUFACTURER_MARGIN = 15


def clean_price(price_str):
    return float(price_str.replace(" TL", "").replace(",", "")) if isinstance(price_str, str) else price_str


def detect_fraudulent_shops(start_date_str, end_date_str):
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    fraudulent_shops = {}
    current_date = start_date

    while current_date <= end_date:
        ref_record = db[REFERENCE_COLLECTION].find_one({"Date": current_date})
        if not ref_record:
            current_date += timedelta(days=1)
            continue

        product_map = {}
        for key in ref_record:
            if key.startswith("Product ") and "Price" not in key:
                product_number = key.split(" ")[1]
                product_name = ref_record[key]
                product_price_key = f"Product {product_number} Price"
                if product_price_key in ref_record:
                    product_price = clean_price(ref_record[product_price_key])
                    product_map[product_name] = product_price

        for shop_name in db.list_collection_names():
            if shop_name in [REFERENCE_COLLECTION, "system.indexes"]:
                continue

            shop_record = db[shop_name].find_one({"Date": current_date})
            if not shop_record:
                continue

            for key in shop_record:
                if key.endswith("Products"):
                    product_group = shop_record[key]
                    for product_key in product_group:
                        if product_key.endswith("Price"):
                            product_number = product_key.replace("Product ", "").replace(" Price", "")
                            product_name_key = f"Product {product_number}"

                            if product_name_key not in product_group:
                                continue

                            product_name = product_group[product_name_key]
                            if product_name not in product_map:
                                continue

                            shop_price = clean_price(product_group[product_key])
                            base_price = product_map[product_name]
                            percentage_diff = ((shop_price - base_price) / base_price) * 100

                            if percentage_diff > TOTAL_THRESHOLD_PERCENTAGE:
                                # Üretici fiyat kontrolü
                                manufacturer_collections = [name for name in db.list_collection_names() if product_name in name or name.endswith("Man")]
                                responsible = "Unknown"

                                for manufacturer_name in manufacturer_collections:
                                    manufacturer_record = db[manufacturer_name].find_one({"Date": current_date})
                                    if not manufacturer_record:
                                        continue

                                    for mkey in manufacturer_record:
                                        if mkey.endswith("Price") and manufacturer_record.get(f"Product {product_number}") == product_name:
                                            manufacturer_price = clean_price(manufacturer_record[mkey])
                                            reduced_price = manufacturer_price / (1 + MANUFACTURER_MARGIN / 100)

                                            if reduced_price > base_price * 1.05:
                                                responsible = "Manufacturer"
                                            else:
                                                responsible = "Shop"
                                            break
                                    if responsible != "Unknown":
                                        break

                                if shop_name not in fraudulent_shops:
                                    fraudulent_shops[shop_name] = {}

                                if product_name not in fraudulent_shops[shop_name]:
                                    fraudulent_shops[shop_name][product_name] = {
                                        "dates": [],
                                        "max_percentage_above": 0,
                                        "responsible": responsible
                                    }

                                fraudulent_shops[shop_name][product_name]["dates"].append(str(current_date.date()))
                                if percentage_diff > fraudulent_shops[shop_name][product_name]["max_percentage_above"]:
                                    fraudulent_shops[shop_name][product_name]["max_percentage_above"] = round(percentage_diff, 2)

        current_date += timedelta(days=1)

    return fraudulent_shops


# Örnek kullanım:
if __name__ == "__main__":
    result = detect_fraudulent_shops("2025-03-01", "2025-03-26")

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
