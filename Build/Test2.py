import pymongo
import pandas as pd
import matplotlib.pyplot as plt

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]


def plot_product_price(product_name, shop_ids):
    """
    Belirli bir ürün için verilen shop'larda tarihsel fiyat değişimini çizer.

    Args:
        product_name (str): Örnek: "Product 177"
        shop_ids (list[int]): Örnek: [6, 14, 11, 33]
    """
    shop_names = [f"Shop {sid}" for sid in shop_ids]
    df_all = []

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
                                    df_all.append({
                                        "Date": date,
                                        "Shop": shop,
                                        "Price": price
                                    })
                                except:
                                    pass

    df = pd.DataFrame(df_all)

    if df.empty:
        print(f"⚠️ Ürün bulunamadı: {product_name}")
        return

    df["Date"] = pd.to_datetime(df["Date"])

    plt.figure(figsize=(12, 6))
    for shop in shop_names:
        sub = df[df["Shop"] == shop].sort_values("Date")
        if not sub.empty:
            print(f"✅ {product_name} bulundu: {shop}")
            plt.plot(sub["Date"], sub["Price"], label=shop)
        else:
            print(f"❌ {product_name} bulunamadı: {shop}")

    plt.title(f"Fiyat Değişimi - {product_name}")
    plt.xlabel("Tarih")
    plt.ylabel("Fiyat (TL)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


plot_product_price("Product 348", [14, 6, 18, 15, 16])
