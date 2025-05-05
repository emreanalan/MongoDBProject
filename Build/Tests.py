import pymongo
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from collections import defaultdict

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# 📦 Collusion ve normal shop grupları
collusion_shops = [
    "Shop 14", "Shop 6", "Shop 18", "Shop 15", "Shop 16",
    "Shop 19", "Shop 7", "Shop 3", "Shop 10", "Shop 11"
]

normal_shops = [
    "Shop 1", "Shop 2", "Shop 4", "Shop 5", "Shop 8",
    "Shop 9", "Shop 12", "Shop 13", "Shop 17", "Shop 20"
]

collusion_group_map = {
    "Shop 14": ["Man 15", "Man 18"],
    "Shop 6":  ["Man 15", "Man 18"],
    "Shop 18": ["Man 15", "Man 18"],
    "Shop 15": ["Man 15", "Man 18"],
    "Shop 16": ["Man 15", "Man 18"],

    "Shop 19": ["Man 5", "Man 2"],
    "Shop 7":  ["Man 5", "Man 2"],
    "Shop 3":  ["Man 5", "Man 2"],
    "Shop 10": ["Man 5", "Man 2"],
    "Shop 11": ["Man 5", "Man 2"]
}

# Ortak üretici ürünlerini topla
def get_common_manufacturer_products(shops, group_map=None):
    result = defaultdict(set)
    for shop in shops:
        cursor = db[shop].find({})
        common_manus = group_map.get(shop, []) if group_map else None
        for doc in cursor:
            for key in doc:
                if key.endswith("Products") and isinstance(doc[key], dict):
                    manu = key.replace(" Products", "")
                    if (not common_manus) or (manu in common_manus):
                        block = doc[key]
                        for i in range(1, 21):
                            pname = block.get(f"Product {i}")
                            if pname:
                                result[pname].add(shop)
    return result

# Ortak ürünü bul
collusion_products = get_common_manufacturer_products(collusion_shops, collusion_group_map)
normal_products = get_common_manufacturer_products(normal_shops)
common_products = set(collusion_products.keys()).intersection(normal_products.keys())

if not common_products:
    print("⚠️ Ortak ürün bulunamadı.")
    exit()

product_common_count = {
    p: len(collusion_products[p]) + len(normal_products[p]) for p in common_products
}
top_product, count = max(product_common_count.items(), key=lambda x: x[1])

collusion_list = sorted(list(collusion_products[top_product]))[:5]
normal_list = sorted(list(normal_products[top_product]))[:5]

print(f"\n🏆 En yaygın ortak ürün: {top_product}")
print(f"📊 Geçtiği toplam shop sayısı: {count}")
print(f"🧠 Collusion shops: {collusion_list}")
print(f"🟦 Normal shops: {normal_list}")

# Fiyatları çek
def extract_price_data(product_name, shop_names):
    data = []
    for shop in shop_names:
        cursor = db[shop].find({})
        for doc in cursor:
            date = doc.get("Date")
            for key in doc:
                if "Products" in key and isinstance(doc[key], dict):
                    block = doc[key]
                    for i in range(1, 21):
                        pname = str(block.get(f"Product {i}", "")).strip().lower()
                        if product_name.strip().lower() in pname:
                            price_str = block.get(f"Product {i} Price")
                            if price_str:
                                try:
                                    price = float(price_str.replace(" TL", "").replace(",", ""))
                                    data.append({"Date": date, "Shop": shop, "Price": price})
                                except:
                                    pass
    return pd.DataFrame(data)

# Grafik çiz
test_cases = [
    {'product': top_product, 'shops': collusion_list},  # collusion
    {'product': top_product, 'shops': normal_list}      # normal
]

fig, axs = plt.subplots(len(test_cases), 1, figsize=(14, 5 * len(test_cases)))
if len(test_cases) == 1:
    axs = [axs]

for i, case in enumerate(test_cases):
    df = extract_price_data(case["product"], case["shops"])
    for shop in case["shops"]:
        if not df[df["Shop"] == shop].empty:
            print(f"✅ {case['product']} bulundu: {shop}")
        else:
            print(f"❌ {case['product']} YOK: {shop}")

    df["Date"] = pd.to_datetime(df["Date"])
    ax = axs[i]
    for shop in case["shops"]:
        sub = df[df["Shop"] == shop].sort_values("Date")
        ax.plot(sub["Date"], sub["Price"], label=shop)
    ax.set_title(f"Fiyat Değişimi - {case['product']} ({'Collusion' if i == 0 else 'Normal'})")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Fiyat (TL)")
    ax.legend()
    ax.grid(True)

plt.tight_layout()
plt.show()
