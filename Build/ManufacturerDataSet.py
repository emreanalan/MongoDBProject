# import pymongo
# import random
#
# # MongoDB bağlantısı
# client = pymongo.MongoClient(
#     "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# )
# db = client["DataSet"]
#
# # Yardımcı Fonksiyonlar
# def get_last_inserted_date(collection):
#     """Verilen koleksiyonda son eklenen tarihi bulur."""
#     last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
#     if last_record:
#         return last_record['Date']
#     return None
#
# def db_manufacturer(manufacturer_name, profit_percentage, *product_names):
#     """Üretici koleksiyonunu oluşturur ve ürünleri ekler."""
#     manufacturer_collection = db[manufacturer_name]
#
#     # Mevcut kayıt varsa ona göre query ayarla
#     last_date_manufacturer = get_last_inserted_date(manufacturer_collection)
#     query = {}
#     if last_date_manufacturer:
#         query = {"Date": {"$gte": last_date_manufacturer}}
#
#     # Ürünleri sırayla ekle
#     for product_name in product_names:
#         products_collection = db["Products"]  # Şimdi tüm ürünler tek collectionda
#         cursor = products_collection.find({"Product Name": product_name, **query}, {"Date": 1, "Cost": 1}).sort("Date", pymongo.ASCENDING)
#
#         for record in cursor:
#             date = record['Date']
#             cost = record['Cost']
#
#             new_price = float(cost.replace(" TL", "").replace(",", "")) * (1 + profit_percentage / 100)
#             new_price_str = f"{new_price:,.2f} TL"
#
#             existing_record = manufacturer_collection.find_one({"Date": date})
#
#             if existing_record:
#                 # Eğer ürün zaten kayıtlıysa ekleme
#                 product_exists = any(
#                     existing_record.get(f"Product {i}") == product_name
#                     for i in range(1, len(existing_record) + 1)
#                     if f"Product {i}" in existing_record
#                 )
#                 if not product_exists:
#                     num_products = len(
#                         [key for key in existing_record.keys() if key.startswith("Product") and "Price" not in key]
#                     )
#                     new_product_index = num_products + 1
#
#                     update_fields = {
#                         f"Product {new_product_index}": product_name,
#                         f"Product {new_product_index} Price": new_price_str,
#                         "Description": f"{existing_record['Description']} and {product_name}",
#                     }
#
#                     manufacturer_collection.update_one({"_id": existing_record["_id"]}, {"$set": update_fields})
#                     print(f"Updated record for {manufacturer_name}: Added {product_name} on {date}.")
#             else:
#                 # Yeni kayıt oluştur
#                 new_record = {
#                     "Date": date,
#                     "Description": product_name,
#                     "Profit Percentage": profit_percentage,
#                     "Product 1": product_name,
#                     "Product 1 Price": new_price_str
#                 }
#                 manufacturer_collection.insert_one(new_record)
#                 print(f"Inserted new record for {manufacturer_name}: Added {product_name} on {date}.")
#
#     print(f"✅ Finished processing manufacturer '{manufacturer_name}'.")
#
# def db_manufacturer_fast_sorted_fixed(manufacturer_name, profit_percentage, *product_names):
#     manufacturer_collection = db[manufacturer_name]
#     products_collection = db["Products"]
#
#     # Tüm ürün kayıtlarını sırayla çekelim
#     all_product_records = []
#     for pname in product_names:
#         records = list(products_collection.find(
#             {"Product Name": pname},
#             {"Product Name": 1, "Date": 1, "Cost": 1}
#         ).sort("Date", pymongo.ASCENDING))
#         all_product_records.append(records)
#
#     # Gün bazlı kayıtları tutalım
#     date_records = {}
#
#     for day_index in range(len(all_product_records[0])):  # 115 gün mesela
#         daily_record = {
#             "Date": all_product_records[0][day_index]["Date"],
#             "Description": "",
#             "Profit Percentage": profit_percentage  # ✨ Hemen Description'dan sonra
#         }
#
#         for idx, product_list in enumerate(all_product_records):
#             product = product_list[day_index]
#             product_name = product["Product Name"]
#             cost = float(product["Cost"].replace(" TL", "").replace(",", "")) * (1 + profit_percentage / 100)
#             cost_str = f"{cost:,.2f} TL"
#
#             daily_record[f"Product {idx+1}"] = product_name
#             daily_record[f"Product {idx+1} Price"] = cost_str
#
#             if idx == 0:
#                 daily_record["Description"] = product_name
#             else:
#                 daily_record["Description"] += f" and {product_name}"
#
#         date_records[daily_record["Date"]] = daily_record
#
#     # Bulk insert
#     bulk_ops = []
#     for date, record in date_records.items():
#         bulk_ops.append(
#             pymongo.UpdateOne(
#                 {"Date": date},
#                 {"$set": record},
#                 upsert=True
#             )
#         )
#
#     if bulk_ops:
#         manufacturer_collection.bulk_write(bulk_ops)
#         print(f"✅ {manufacturer_name}: {len(bulk_ops)} kayıt işlendi (düzeltilmiş ve sıralı).")
#
# # --- Ana Program ---
#
# all_products = [f"Product {i}" for i in range(1, 501)]  # Product 1-500
#
# for i in range(25):  # 25 Manufacturer
#     manufacturer_name = f"Man{i+1}"
#     assigned_products = all_products[i*20 : (i+1)*20]
#     profit_percentage = random.randint(2, 12)
#     db_manufacturer_fast_sorted_fixed(manufacturer_name, profit_percentage, *assigned_products)
#
#
import pymongo
import random

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# Yardımcı Fonksiyonlar
def get_last_inserted_date(collection):
    """Verilen koleksiyonda son eklenen tarihi bulur."""
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None

def get_production_rate_and_profit():
    rate = random.choice(["Low", "Moderate", "High"])
    if rate == "Low":
        return rate, round(random.uniform(2.0, 4.0), 2), 1.00
    elif rate == "Moderate":
        return rate, round(random.uniform(6.5, 9.0), 2), 0.95
    else:
        return rate, round(random.uniform(11.0, 13.5), 2), 0.90

def db_manufacturer_fast_sorted_fixed(manufacturer_name, production_rate, profit_percentage, cost_multiplier, *product_names):
    manufacturer_collection = db[manufacturer_name]
    products_collection = db["Products"]

    # Tüm ürün kayıtlarını sırayla çekelim
    all_product_records = []
    for pname in product_names:
        records = list(products_collection.find(
            {"Product Name": pname},
            {"Product Name": 1, "Date": 1, "Cost": 1}
        ).sort("Date", pymongo.ASCENDING))
        all_product_records.append(records)

    # Gün bazlı kayıtları tutalım
    date_records = {}

    for day_index in range(len(all_product_records[0])):
        daily_record = {
            "Date": all_product_records[0][day_index]["Date"],
            "Description": "",
            "Production Rate": production_rate,
            "Profit Percentage": profit_percentage
        }

        for idx, product_list in enumerate(all_product_records):
            product = product_list[day_index]
            product_name = product["Product Name"]
            base_cost = float(product["Cost"].replace(" TL", "").replace(",", ""))

            cost_price = base_cost * cost_multiplier
            final_price = cost_price * (1 + profit_percentage / 100)

            cost_price_str = f"{cost_price:,.2f} TL"
            final_price_str = f"{final_price:,.2f} TL"

            daily_record[f"Product {idx+1}"] = product_name
            daily_record[f"Product {idx+1} Cost Price"] = cost_price_str
            daily_record[f"Product {idx+1} Price"] = final_price_str

            if idx == 0:
                daily_record["Description"] = product_name
            else:
                daily_record["Description"] += f" and {product_name}"

        date_records[daily_record["Date"]] = daily_record

    # Bulk insert
    bulk_ops = []
    for date, record in date_records.items():
        bulk_ops.append(
            pymongo.UpdateOne(
                {"Date": date},
                {"$set": record},
                upsert=True
            )
        )

    if bulk_ops:
        manufacturer_collection.bulk_write(bulk_ops)
        print(f"✅ {manufacturer_name}: {len(bulk_ops)} kayıt işlendi (Production Rate: {production_rate}, Profit %: {profit_percentage}).")

# --- Ana Program ---

all_products = [f"Product {i}" for i in range(1, 501)]  # Product 1-500

for i in range(25):  # 25 Manufacturer
    manufacturer_name = f"Man {i+1}"
    assigned_products = all_products[i*20 : (i+1)*20]
    production_rate, profit_percentage, cost_multiplier = get_production_rate_and_profit()
    db_manufacturer_fast_sorted_fixed(manufacturer_name, production_rate, profit_percentage, cost_multiplier, *assigned_products)
