# import pymongo
# import random
# from datetime import datetime, timedelta
#
# # MongoDB bağlantısı
# client = pymongo.MongoClient(
#     "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
#     serverSelectionTimeoutMS=300000,  # 5 dakika
#     socketTimeoutMS=600000,            # 10 dakika
#     connectTimeoutMS=300000
# )
# db = client["DataSet"]
#
# # === 1. Products Cache ===
# print("🔵 Products cache oluşturuluyor...")
# products_collection = db["Products"]
# product_cursor = products_collection.find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
# products_cache = {(p["Product Name"], p["Date"]): p["Cost"] for p in product_cursor}
# print(f"✅ {len(products_cache)} ürün kaydı cache'lendi.\n")
#
# # === 2. Manufacturers Cache (YENİ) ===
# print("🔵 Manufacturers cache oluşturuluyor...")
# manufacturers = [f"Man {i}" for i in range(1, 26)]
# manufacturers_cache = {}
#
# start_date = datetime(2025, 1, 1)
# end_date = start_date + timedelta(days=114)
#
# for manu in manufacturers:
#     print(f"  🔹 {manu} cache'leniyor...")
#     manu_cursor = db[manu].find(
#         {"Date": {"$gte": start_date, "$lte": end_date}},
#         {"_id": 0}  # _id alma
#     )
#     manu_data = {}
#     for record in manu_cursor:
#         date = record["Date"]
#         manu_data[date] = record
#     manufacturers_cache[manu] = manu_data
#
# print(f"✅ {len(manufacturers_cache)} manufacturer cache'lendi.\n")
#
# # === 3. Tarihler ===
# all_dates = [start_date + timedelta(days=i) for i in range(115)]
#
# def generate_normal_shop_data(shop_id_list):
#     print("🚀 ShopsDataSet oluşturuluyor...\n")
#
#     for shop_num in shop_id_list:
#         shop_name = f"Shop {shop_num}"
#         shop_collection = db[shop_name]
#
#         selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))
#         print(f"🔵 {shop_name} için seçilen manufacturerlar: {selected_manufacturers}")
#
#         product_profits = {}
#         zam_days = sorted(random.sample(range(5, 110), k=random.randint(2, 5)))
#         print(f"  📅 {shop_name} zam günleri: {[all_dates[day].strftime('%Y-%m-%d') for day in zam_days]}")
#
#         bulk_operations = []
#         previous_prices = {}
#
#         for day_idx, current_date in enumerate(all_dates):
#             shop_doc = {
#                 "Date": current_date,
#                 "Store Type": shop_name,
#                 "Description": f"Product prices for {shop_name} on {current_date.strftime('%Y-%m-%d')}",
#             }
#
#             for manu in selected_manufacturers:
#                 manu_data = manufacturers_cache[manu].get(current_date)
#                 if not manu_data:
#                     continue
#
#                 manu_doc = {}
#                 product_keys = sorted(
#                     [k for k in manu_data.keys() if k.startswith("Product ") and "Price" not in k],
#                     key=lambda x: int(x.split()[1])
#                 )
#
#                 for i, prod_key in enumerate(product_keys):
#                     pname = manu_data[prod_key]
#                     price_str = manu_data.get(f"{prod_key} Price")
#
#                     if not price_str:
#                         continue
#
#                     manufacturer_price = float(price_str.replace(",", "").replace(" TL", ""))
#
#                     if pname not in product_profits:
#                         product_profits[pname] = random.randint(4, 15)
#
#                     profit_pct = product_profits[pname] / 100
#
#                     if day_idx == 0:
#                         shop_price = manufacturer_price * (1 + profit_pct)
#                         previous_prices[pname] = shop_price
#                     elif day_idx in zam_days:
#                         shop_price = manufacturer_price * (1 + profit_pct)
#                         previous_prices[pname] = shop_price
#                     else:
#                         shop_price = previous_prices.get(pname, manufacturer_price * (1 + profit_pct))
#
#                     manu_doc[f"Product {i+1}"] = pname
#                     manu_doc[f"Product {i+1} Price"] = f"{shop_price:,.2f} TL"
#
#                 if manu_doc:
#                     shop_doc[f"{manu} Products"] = manu_doc
#
#             if shop_doc:
#                 bulk_operations.append(pymongo.UpdateOne({"Date": current_date}, {"$set": shop_doc}, upsert=True))
#
#         if bulk_operations:
#             shop_collection.bulk_write(bulk_operations)
#             print(f"✅ {shop_name} için {len(bulk_operations)} kayıt eklendi.\n")
#         else:
#             print(f"⚠️ {shop_name} için hiç veri eklenmedi.\n")
#
#     print("\n✅ Tüm ShopsDataSet kayıtları başarıyla tamamlandı!")
import pymongo
import random
from datetime import datetime, timedelta

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,
    socketTimeoutMS=600000,
    connectTimeoutMS=300000
)
db = client["DataSet"]

# === 1. Products Cache ===
print("🔵 Products cache oluşturuluyor...")
products_collection = db["Products"]
product_cursor = products_collection.find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
products_cache = {(p["Product Name"], p["Date"]): p["Cost"] for p in product_cursor}
print(f"✅ {len(products_cache)} ürün kaydı cache'lendi.\n")

# === 2. Manufacturers Cache ===
print("🔵 Manufacturers cache oluşturuluyor...")
manufacturers = [f"Man {i}" for i in range(1, 26)]
manufacturers_cache = {}
manufacturer_product_profit_cache = {}  # ⚡️ Yeni cache

start_date = datetime(2025, 1, 1)
end_date = start_date + timedelta(days=114)

for manu in manufacturers:
    print(f"  🔹 {manu} cache'leniyor...")
    manu_cursor = db[manu].find(
        {"Date": {"$gte": start_date, "$lte": end_date}},
        {"_id": 0}
    )
    manu_data = {}
    for record in manu_cursor:
        date = record["Date"]
        manu_data[date] = record

        for k in record:
            if k.startswith("Product ") and "Price" not in k:
                pname = record[k]
                if manu not in manufacturer_product_profit_cache:
                    manufacturer_product_profit_cache[manu] = {}
                if pname not in manufacturer_product_profit_cache[manu]:
                    manufacturer_product_profit_cache[manu][pname] = round(random.uniform(2.0, 12.0), 2)

    manufacturers_cache[manu] = manu_data

print(f"✅ {len(manufacturers_cache)} manufacturer cache'lendi.\n")

# === 3. Tarihler ===
all_dates = [start_date + timedelta(days=i) for i in range(115)]

def generate_normal_shop_data(shop_id_list):
    print("🚀 ShopsDataSet oluşturuluyor...\n")

    for shop_num in shop_id_list:
        shop_name = f"Shop {shop_num}"
        shop_collection = db[shop_name]

        selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))
        print(f"🔵 {shop_name} için seçilen manufacturerlar: {selected_manufacturers}")

        zam_days = sorted(random.sample(range(5, 110), k=random.randint(2, 5)))
        print(f"  📅 {shop_name} zam günleri: {[all_dates[day].strftime('%Y-%m-%d') for day in zam_days]}")

        bulk_operations = []
        previous_prices = {}

        # Bu shop'a özel sapmalı profit cache
        shop_profit_variation = {}
        for manu in selected_manufacturers:
            for pname, base_profit in manufacturer_product_profit_cache[manu].items():
                variation = round(random.uniform(-0.1, 0.1), 3)  # ± 0.1 sapma
                adjusted_profit = round(base_profit + variation, 2)
                if shop_name not in shop_profit_variation:
                    shop_profit_variation[shop_name] = {}
                shop_profit_variation[shop_name][(manu, pname)] = adjusted_profit

        for day_idx, current_date in enumerate(all_dates):
            shop_doc = {
                "Date": current_date,
                "Store Type": shop_name,
                "Description": f"Product prices for {shop_name} on {current_date.strftime('%Y-%m-%d')}",
            }

            for manu in selected_manufacturers:
                manu_data = manufacturers_cache[manu].get(current_date)
                if not manu_data:
                    continue

                manu_doc = {}
                product_keys = sorted(
                    [k for k in manu_data.keys() if k.startswith("Product ") and "Price" not in k],
                    key=lambda x: int(x.split()[1])
                )

                for i, prod_key in enumerate(product_keys):
                    pname = manu_data[prod_key]
                    price_str = manu_data.get(f"{prod_key} Price")

                    if not price_str:
                        continue

                    manufacturer_price = float(price_str.replace(",", "").replace(" TL", ""))
                    shop_profit_pct = shop_profit_variation[shop_name].get((manu, pname), random.uniform(2.0, 12.0))

                    if day_idx == 0 or day_idx in zam_days:
                        shop_price = manufacturer_price * (1 + shop_profit_pct / 100)
                        previous_prices[pname] = shop_price
                    else:
                        shop_price = previous_prices.get(pname, manufacturer_price * (1 + shop_profit_pct / 100))

                    manu_doc[f"Product {i+1}"] = pname
                    manu_doc[f"Product {i+1} Manufacturer Price"] = f"{manufacturer_price:,.2f} TL"
                    manu_doc[f"Product {i+1} Shop Profit %"] = shop_profit_pct
                    manu_doc[f"Product {i+1} Price"] = f"{shop_price:,.2f} TL"

                if manu_doc:
                    shop_doc[f"{manu} Products"] = manu_doc

            if shop_doc:
                bulk_operations.append(pymongo.UpdateOne({"Date": current_date}, {"$set": shop_doc}, upsert=True))

        if bulk_operations:
            shop_collection.bulk_write(bulk_operations)
            print(f"✅ {shop_name} için {len(bulk_operations)} kayıt eklendi.\n")
        else:
            print(f"⚠️ {shop_name} için hiç veri eklenmedi.\n")

    print("\n✅ Tüm ShopsDataSet kayıtları başarıyla tamamlandı!")

# --- Shops oluşturuluyor ---
generate_normal_shop_data([1, 2])
