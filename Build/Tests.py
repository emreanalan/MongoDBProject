import pymongo
from datetime import datetime, timedelta

# === MongoDB Bağlantısı === #
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,
    socketTimeoutMS=600000,
    connectTimeoutMS=300000
)
db = client["DataSet"]

# === Parametreler === #
shop_list = [f"Shop {i}" for i in range(1, 9)]
price_delta_threshold = 0.01  # %1 fark
minimum_match_days = 3
minimum_common_products = 5

# === Yardımcı Fonksiyon === #
def extract_price(price_str):
    if not price_str:
        return None
    return float(price_str.replace(" TL", "").replace(",", ""))

def detect_collusion():
    collusion_scores = {}

    for i, shop_a in enumerate(shop_list):
        for shop_b in shop_list[i+1:]:
            match_count = 0
            product_overlap = {}

            cursor_a = db[shop_a].find({}, {"Date": 1})
            all_dates = sorted([doc["Date"] for doc in cursor_a if "Date" in doc])

            for date in all_dates:
                doc_a = db[shop_a].find_one({"Date": date})
                doc_b = db[shop_b].find_one({"Date": date})
                if not doc_a or not doc_b:
                    continue

                for key in doc_a:
                    if "Products" in key:
                        manu_a = doc_a.get(key, {})
                        manu_b = doc_b.get(key, {})
                        for i in range(1, 21):
                            p_key = f"Product {i}"
                            p_price_a = extract_price(manu_a.get(f"{p_key} Price"))
                            p_price_b = extract_price(manu_b.get(f"{p_key} Price"))
                            if p_price_a and p_price_b:
                                diff = abs(p_price_a - p_price_b) / max(p_price_a, p_price_b)
                                if diff <= price_delta_threshold:
                                    product_name = manu_a[p_key]
                                    product_overlap.setdefault(date, []).append(product_name)

            for date, prods in product_overlap.items():
                if len(prods) >= minimum_common_products:
                    match_count += 1

            if match_count >= minimum_match_days:
                collusion_scores[(shop_a, shop_b)] = match_count

    print("\n🔍 Tespit Edilen Potansiyel Collusion Çiftleri:")
    for (a, b), score in sorted(collusion_scores.items(), key=lambda x: -x[1]):
        print(f"  ⚠️ {a} & {b} -> {score} ortak gün")

if __name__ == "__main__":
    detect_collusion()
