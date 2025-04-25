import pymongo
import random
from datetime import datetime

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

products_collection = db["Products"]

# 📥 Tüm Products koleksiyonunu çekip hafızaya alıyoruz
print("🔵 Products cache oluşturuluyor...")
products_cursor = products_collection.find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
products_cache = {}

for record in products_cursor:
    date = record["Date"]
    name = record["Product Name"]
    cost = record["Cost"]
    products_cache[(name, date)] = cost

print(f"✅ {len(products_cache)} ürün kaydı cache'lendi.\n")

manufacturers = [f"Man{i}" for i in range(1, 26)]

print("🚀 ShopsDataSet oluşturuluyor...\n")

for shop_num in range(31, 91):
    shop_name = f"Shop {shop_num}"
    shop_collection = db[shop_name]

    selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))
    print(f"🔵 {shop_name} için seçilen manufacturerlar: {selected_manufacturers}")

    bulk_operations = []
    dates_cursor = db[selected_manufacturers[0]].find({}, {"Date": 1}).sort("Date", pymongo.ASCENDING)

    for date_record in dates_cursor:
        date = date_record["Date"]
        print(f"  📅 İşleniyor: {shop_name} için tarih {date}")

        shop_doc = {
            "Date": date,
            "Store Type": shop_name,
            "Description": f"Product prices for {shop_name} as of {date.strftime('%Y-%m-%d')}",
        }

        for manu in selected_manufacturers:
            manu_record = db[manu].find_one({"Date": date})
            if not manu_record:
                continue

            manufacturer_doc = {}
            product_keys = sorted(
                [k for k in manu_record.keys() if k.startswith("Product ") and "Price" not in k],
                key=lambda x: int(x.split()[1])
            )

            product_counter = 1
            for key in product_keys:
                product_name = manu_record[key]
                profit = random.randint(2, 12)

                cost = products_cache.get((product_name, date))
                if cost:
                    base_cost = float(cost.replace(" TL", "").replace(",", ""))
                    final_price = base_cost * (1 + profit / 100)

                    manufacturer_doc[f"Product {product_counter}"] = product_name
                    manufacturer_doc[f"Product {product_counter} Price"] = f"{final_price:,.2f} TL"
                    product_counter += 1

            if manufacturer_doc:
                shop_doc[f"{manu} Products"] = manufacturer_doc

        if shop_doc:
            bulk_operations.append(
                pymongo.UpdateOne({"Date": date}, {"$set": shop_doc}, upsert=True)
            )

    if bulk_operations:
        shop_collection.bulk_write(bulk_operations)
        print(f"✅ {shop_name} için {len(bulk_operations)} kayıt eklendi.\n")
    else:
        print(f"⚠️ {shop_name} için hiç veri eklenmedi.\n")

print("\n✅ Tüm ShopsDataSet kayıtları ultra hızlı şekilde tamamlandı!")
