import pymongo
import matplotlib.pyplot as plt
from datetime import datetime

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

def plot_product_price_history(product_name, shop_names):
    plt.figure(figsize=(12, 6))

    for shop in shop_names:
        collection = db[shop]
        cursor = collection.find({}, {"_id": 0, "Date": 1})

        dates = []
        prices = []

        for doc in sorted(cursor, key=lambda d: d["Date"]):
            for key in doc:
                if "Products" in key:
                    manu_products = doc[key]
                    for i in range(1, 21):
                        pname = manu_products.get(f"Product {i}")
                        if pname == product_name:
                            price_str = manu_products.get(f"Product {i} Price")
                            if price_str:
                                price = float(price_str.replace(" TL", "").replace(".", "").replace(",", "."))
                                dates.append(doc["Date"])
                                prices.append(price)
                            break

        if dates and prices:
            plt.plot(dates, prices, label=shop)

    plt.xlabel("Tarih")
    plt.ylabel("Fiyat (TL)")
    plt.title(f"Ürün Fiyat Grafiği: {product_name}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Örnek kullanım
product_name = "Product 321"
shop_names = ["Shop 28", "Shop 70", "Shop 37", "Shop 53", "Shop 87"]
plot_product_price_history(product_name, shop_names)
