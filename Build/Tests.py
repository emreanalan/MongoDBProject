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
    {'product': 'Product 75', 'shops': ['Shop 10', 'Shop 12', 'Shop 14', 'Shop 19', 'Shop 24']},  # collusion
    {'product': 'Product 75', 'shops': ['Shop 2', 'Shop 20', 'Shop 29', 'Shop 35', 'Shop 44']}   # normal
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
# collusion_shops = [
#     "Shop 69", "Shop 4", "Shop 100", "Shop 55",
#     "Shop 21", "Shop 97", "Shop 33", "Shop 43", "Shop 64",
#     "Shop 90", "Shop 28", "Shop 14", "Shop 58", "Shop 78",
#     "Shop 99", "Shop 74", "Shop 48", "Shop 63", "Shop 30",
#     "Shop 7", "Shop 36", "Shop 23", "Shop 37",
#     "Shop 67", "Shop 57", "Shop 39", "Shop 24", "Shop 12",
#     "Shop 13", "Shop 54", "Shop 34", "Shop 76", "Shop 47",
#     "Shop 9", "Shop 19", "Shop 61", "Shop 70", "Shop 10",
#     "Shop 83", "Shop 91", "Shop 41", "Shop 80",
#     "Shop 17", "Shop 68", "Shop 22", "Shop 15", "Shop 79",
#     "Shop 8", "Shop 45", "Shop 5"
# ]
#
#
# normal_shops = [
#     "Shop 1", "Shop 2", "Shop 3", "Shop 6", "Shop 11", "Shop 16", "Shop 18",
#     "Shop 20", "Shop 25", "Shop 26", "Shop 27", "Shop 29", "Shop 31", "Shop 32",
#     "Shop 35", "Shop 38", "Shop 40", "Shop 42", "Shop 44", "Shop 46", "Shop 49",
#     "Shop 50", "Shop 51", "Shop 52", "Shop 53", "Shop 56", "Shop 59", "Shop 60",
#     "Shop 62", "Shop 65", "Shop 66", "Shop 71", "Shop 72", "Shop 73", "Shop 75",
#     "Shop 77", "Shop 81", "Shop 82", "Shop 84", "Shop 85", "Shop 86", "Shop 87",
#     "Shop 88", "Shop 89", "Shop 92", "Shop 93", "Shop 94", "Shop 95", "Shop 96",
#     "Shop 98"
# ]
#
#
# collusion_group_map = {
#     "Shop 69": ["Man 13", "Man 19"],
#     "Shop 4": ["Man 13", "Man 19"],
#     "Shop 100": ["Man 13", "Man 19"],
#     "Shop 55": ["Man 13", "Man 19"],
#     "Shop 21": ["Man 23", "Man 24"],
#     "Shop 97": ["Man 23", "Man 24"],
#     "Shop 33": ["Man 23", "Man 24"],
#     "Shop 43": ["Man 23", "Man 24"],
#     "Shop 64": ["Man 23", "Man 24"],
#     "Shop 90": ["Man 10", "Man 4"],
#     "Shop 28": ["Man 10", "Man 4"],
#     "Shop 14": ["Man 10", "Man 4"],
#     "Shop 58": ["Man 10", "Man 4"],
#     "Shop 78": ["Man 10", "Man 4"],
#     "Shop 99": ["Man 9", "Man 13"],
#     "Shop 74": ["Man 9", "Man 13"],
#     "Shop 48": ["Man 9", "Man 13"],
#     "Shop 63": ["Man 9", "Man 13"],
#     "Shop 30": ["Man 9", "Man 13"],
#     "Shop 7": ["Man 14", "Man 25"],
#     "Shop 36": ["Man 14", "Man 25"],
#     "Shop 23": ["Man 14", "Man 25"],
#     "Shop 37": ["Man 14", "Man 25"],
#     "Shop 67": ["Man 21", "Man 4"],
#     "Shop 57": ["Man 21", "Man 4"],
#     "Shop 39": ["Man 21", "Man 4"],
#     "Shop 24": ["Man 21", "Man 4"],
#     "Shop 12": ["Man 21", "Man 4"],
#     "Shop 13": ["Man 23", "Man 21"],
#     "Shop 54": ["Man 23", "Man 21"],
#     "Shop 34": ["Man 23", "Man 21"],
#     "Shop 76": ["Man 23", "Man 21"],
#     "Shop 47": ["Man 23", "Man 21"],
#     "Shop 9": ["Man 3", "Man 4"],
#     "Shop 19": ["Man 3", "Man 4"],
#     "Shop 61": ["Man 3", "Man 4"],
#     "Shop 70": ["Man 3", "Man 4"],
#     "Shop 10": ["Man 3", "Man 4"],
#     "Shop 83": ["Man 16", "Man 21"],
#     "Shop 91": ["Man 16", "Man 21"],
#     "Shop 41": ["Man 16", "Man 21"],
#     "Shop 80": ["Man 16", "Man 21"],
#     "Shop 17": ["Man 3", "Man 24"],
#     "Shop 68": ["Man 3", "Man 24"],
#     "Shop 22": ["Man 3", "Man 24"],
#     "Shop 15": ["Man 3", "Man 24"],
#     "Shop 79": ["Man 3", "Man 24"],
#     "Shop 8": ["Man 10", "Man 20"],
#     "Shop 45": ["Man 10", "Man 20"],
#     "Shop 5": ["Man 10", "Man 20"]
# }
#
#
#
# def get_common_manufacturer_products(shops, group_map=None):
#     result = defaultdict(set)  # product -> set of shops
#     for shop in shops:
#         cursor = db[shop].find({})
#         common_manus = group_map.get(shop, []) if group_map else None
#         for doc in cursor:
#             for key in doc:
#                 if key.endswith("Products") and isinstance(doc[key], dict):
#                     manu = key.replace(" Products", "")
#                     if (not common_manus) or (manu in common_manus):  # sadece ortak üretici ise
#                         block = doc[key]
#                         for i in range(1, 21):
#                             pname = block.get(f"Product {i}")
#                             if pname:
#                                 result[pname].add(shop)
#     return result
#
# # 1. Verileri al
# collusion_products = get_common_manufacturer_products(collusion_shops, collusion_group_map)
# normal_products = get_common_manufacturer_products(normal_shops)
#
# # 2. Ortak ürünleri bul
# common_products = set(collusion_products.keys()).intersection(normal_products.keys())
# if not common_products:
#     print("⚠️ Ortak ürün bulunamadı. Lütfen üretici tanım koşullarını kontrol edin.")
#     exit()
#
# # 3. En yaygın ürünü bul
# product_common_count = {
#     p: len(collusion_products[p]) + len(normal_products[p]) for p in common_products
# }
# top_product, count = max(product_common_count.items(), key=lambda x: x[1])
#
# # 4. Shop listelerini hazırla
# collusion_list = sorted(list(collusion_products[top_product]))[:5]
# normal_list = sorted(list(normal_products[top_product]))[:5]
#
# # 5. Yazdır
# print(f"\n🏆 En yaygın ortak ürün: {top_product}")
# print(f"📊 Geçtiği toplam shop sayısı: {count}")
#
# print("\n📦 Otomatik Test Case:")
# print("test_cases = [")
# print(f"    {{'product': '{top_product}', 'shops': {collusion_list}}},  # collusion")
# print(f"    {{'product': '{top_product}', 'shops': {normal_list}}}   # normal")
# print("]")

