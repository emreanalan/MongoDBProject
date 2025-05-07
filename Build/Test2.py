import pymongo
import pandas as pd
import matplotlib.pyplot as plt

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

product_name = "Product 301"
shop_ids = [45]
shop_names = [f"Shop {i}" for i in shop_ids]

records = []

for shop_name in shop_names:
    collection = db[shop_name]
    cursor = collection.find()

    for doc in cursor:
        date = doc.get("Date")
        for key in doc.keys():
            if key.startswith("Man") and "Products" in key:
                man_products = doc[key]
                product_key = product_name
                price_key = f"{product_name} Price"

                if product_key in man_products and price_key in man_products:
                    price_str = man_products[price_key].replace(" TL", "").replace(",", "")
                    try:
                        price = float(price_str)
                        records.append({
                            "date": pd.to_datetime(date),
                            "shop_name": shop_name,
                            "price": price
                        })
                    except ValueError:
                        print(f"Fiyat dönüştürülemedi: {price_str} ({shop_name} / {date})")

# DataFrame'e aktar
df = pd.DataFrame(records)

# Eğer veri boşsa hata verme
if df.empty:
    print("Uyarı: Belirtilen ürün için hiçbir mağazada veri bulunamadı.")
else:
    # Grafiği çiz
    plt.figure(figsize=(12, 6))
    for shop_name in shop_names:
        shop_df = df[df["shop_name"] == shop_name]
        plt.plot(shop_df["date"], shop_df["price"], label=shop_name)

    plt.title(f"Fiyat-Zaman Grafiği - {product_name}")
    plt.xlabel("Tarih")
    plt.ylabel("Fiyat (TL)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
