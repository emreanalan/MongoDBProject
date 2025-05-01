import pymongo
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from collections import defaultdict

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

test_cases = [
    {'product': 'Product 287', 'shops': ['Shop 27', 'Shop 30', 'Shop 55', 'Shop 92']},  # collusion
    {'product': 'Product 287', 'shops': ['Shop 22', 'Shop 34']}   # normal
]
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
                        pname = block.get(f"Product {i}")
                        if pname == product_name:
                            price_str = block.get(f"Product {i} Price")
                            if price_str:
                                price = float(price_str.replace(" TL", "").replace(",", ""))
                                data.append({"Date": date, "Shop": shop, "Price": price})
    return pd.DataFrame(data)



# Grafik çiz
fig, axs = plt.subplots(len(test_cases), 1, figsize=(14, 5 * len(test_cases)))

if len(test_cases) == 1:
    axs = [axs]

for i, case in enumerate(test_cases):
    df = extract_price_data(case["product"], case["shops"])
    # Hangi shoplarda ürün gerçekten bulunmuş?
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
    ax.set_title(f"Fiyat Değişimi - {case['product']}")
    ax.set_xlabel("Tarih")
    ax.set_ylabel("Fiyat (TL)")
    ax.legend()
    ax.grid(True)

plt.tight_layout()
plt.show()




# Shop grupları
# collusion_shops = ["Shop 55", "Shop 27", "Shop 30", "Shop 92"]
# normal_shops = ["Shop 34", "Shop 60", "Shop 12", "Shop 9", "Shop 22"]
#
# def product_counts(shop_list):
#     product_freq = defaultdict(set)
#     for shop in shop_list:
#         cursor = db[shop].find({})
#         for doc in cursor:
#             for key in doc:
#                 if "Products" in key and isinstance(doc[key], dict):
#                     block = doc[key]
#                     for i in range(1, 21):
#                         pname = block.get(f"Product {i}")
#                         if pname:
#                             product_freq[pname].add(shop)
#     return product_freq
#
# collusion_counts = product_counts(collusion_shops)
# normal_counts = product_counts(normal_shops)
#
# common_products = set(collusion_counts.keys()).intersection(normal_counts.keys())
# product_common_count = {
#     p: len(collusion_counts[p]) + len(normal_counts[p])
#     for p in common_products
# }
# top_product, count = max(product_common_count.items(), key=lambda x: x[1])
#
# print(f"\n🏆 En yaygın ortak ürün: {top_product}")
# print(f"📊 Geçtiği toplam shop sayısı: {count}")
#
# # Test case oluştur
# collusion_list = sorted(list(collusion_counts[top_product]))[:5]
# normal_list = sorted(list(normal_counts[top_product]))[:5]
#
# print("\n📦 Otomatik Test Case:")
# print("test_cases = [")
# print(f"    {{'product': '{top_product}', 'shops': {collusion_list}}},  # collusion")
# print(f"    {{'product': '{top_product}', 'shops': {normal_list}}}   # normal")
# print("]")

