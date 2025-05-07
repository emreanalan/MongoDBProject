import pymongo
import random

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]


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

def calculate_cournot_price(Q, a=1000, b=0.1):
    return max(0, a - b * Q)

def get_total_quantity(product_name, date, competitors):
    total = 0
    for comp in competitors:
        coll = db[comp]
        doc = coll.find_one({"Date": date})
        if doc:
            for key in doc:
                if key.startswith("Product") and doc[key] == product_name:
                    produced_key = key + " Produced Quantity"
                    if produced_key in doc:
                        total += doc[produced_key]
    return total

def db_manufacturer_fast_sorted_fixed(manufacturer_name, production_rate, profit_percentage, cost_multiplier, *product_names):
    manufacturer_collection = db[manufacturer_name]
    products_collection = db["Products"]

    all_product_records = []
    for pname in product_names:
        records = list(products_collection.find(
            {"Product Name": pname},
            {"Product Name": 1, "Date": 1, "Cost": 1, "Market Price Function": 1, "Cournot Competitors": 1}
        ).sort("Date", pymongo.ASCENDING))
        all_product_records.append(records)

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
            competitors = product.get("Cournot Competitors", [])
            if manufacturer_name not in competitors:
                competitors.append(manufacturer_name)  # kendini dahil et

            a, b = 1000, 0.1  # default değer
            if "Market Price Function" in product:
                try:
                    fn = product["Market Price Function"]
                    a = float(fn.split("=")[1].split("-")[0].strip())
                    b = float(fn.split("-")[1].split("*")[0].strip())
                except:
                    pass  # varsayılan kalsın

            # Cournot miktarları ve fiyat
            produced_qty = random.randint(100, 500)
            others_qty = get_total_quantity(product_name, product["Date"], competitors)
            total_qty = produced_qty + others_qty
            market_price = calculate_cournot_price(total_qty, a, b)

            # Maliyet, gelir, kâr
            cost_price = base_cost * cost_multiplier
            revenue = produced_qty * market_price
            profit = revenue - (produced_qty * cost_price)

            # Formatlı değerler
            cost_price_str = f"{cost_price:,.2f} TL"
            market_price_str = f"{market_price:,.2f} TL"
            revenue_str = f"{revenue:,.2f} TL"
            profit_str = f"{profit:,.2f} TL"

            # Mongo'ya kayıt için
            prefix = f"Product {idx+1}"
            daily_record[prefix] = product_name
            daily_record[f"{prefix} Cost Price"] = cost_price_str
            daily_record[f"{prefix} Produced Quantity"] = produced_qty
            daily_record[f"{prefix} Total Quantity"] = total_qty
            daily_record[f"{prefix} Market Price"] = market_price_str
            daily_record[f"{prefix} Revenue"] = revenue_str
            daily_record[f"{prefix} Profit"] = profit_str

            if idx == 0:
                daily_record["Description"] = product_name
            else:
                daily_record["Description"] += f" and {product_name}"

        date_records[daily_record["Date"]] = daily_record

    # MongoDB’ye toplu yazma
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
        print(f"✅ {manufacturer_name}: {len(bulk_ops)} kayıt işlendi (Cournot dahil).")


# --- Ana Program ---

all_products = [f"Product {i}" for i in range(1, 501)]

for i in range(25):  # 25 Manufacturer
    manufacturer_name = f"Man {i+26}"  # 26'dan başlıyor
    assigned_products = all_products[i*20 : (i+1)*20]
    production_rate, profit_percentage, cost_multiplier = get_production_rate_and_profit()
    db_manufacturer_fast_sorted_fixed(manufacturer_name, production_rate, profit_percentage, cost_multiplier, *assigned_products)

