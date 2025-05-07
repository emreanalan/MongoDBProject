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
