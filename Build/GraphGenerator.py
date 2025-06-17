import pandas as pd
import matplotlib.pyplot as plt
import pymongo
from datetime import datetime
import matplotlib.dates as mdates

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]
products_collection = db["Products"]

def get_product_price_data(product_name):
    cursor = products_collection.find(
        {"Product Name": product_name},
        {"_id": 0, "Date": 1, "Cost": 1}
    ).sort("Date", pymongo.ASCENDING)

    data = list(cursor)
    if not data:
        return None

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Cost"] = df["Cost"].str.replace(" TL", "").str.replace(",", "").astype(float)
    return df


def plot_product_price(product_name):
    df = get_product_price_data(product_name)
    if df is None:
        print(f"{product_name} için veri bulunamadı.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df["Date"], df["Cost"], label=product_name, linewidth=2)
    plt.title(f"{product_name} - Fiyat Zaman Grafiği")
    plt.xlabel("Tarih")
    plt.ylabel("Fiyat (TL)")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def get_manufacturer_data(manufacturer_name, product_name):
    collection = db[manufacturer_name]
    cursor = collection.find(
        {f"Product 1": product_name},
        {"_id": 0, "Date": 1,
         "Product 1 Cost Price": 1,
         "Product 1 Market Price": 1,
         "Product 1 Profit": 1}
    ).sort("Date", pymongo.ASCENDING)

    data = list(cursor)
    if not data:
        return None

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Cost Price"] = df["Product 1 Cost Price"].str.replace(" TL", "").str.replace(",", "").astype(float)
    df["Market Price"] = df["Product 1 Market Price"].str.replace(" TL", "").str.replace(",", "").astype(float)
    df["Profit"] = df["Product 1 Profit"].str.replace(" TL", "").str.replace(",", "").astype(float)
    return df


def plot_manufacturer_product_prices(manufacturer_name, product_name):
    df = get_manufacturer_data(manufacturer_name, product_name)
    if df is None:
        print(f"{manufacturer_name} üreticisi için {product_name} verisi bulunamadı.")
        return

    plt.figure(figsize=(14, 6))
    plt.plot(df["Date"], df["Cost Price"], label="Maliyet Fiyatı", linestyle='--')
    plt.plot(df["Date"], df["Market Price"], label="Pazar Fiyatı", linestyle='-')
    plt.plot(df["Date"], df["Profit"], label="Kâr", linestyle=':', linewidth=2)

    plt.title(f"{manufacturer_name} - {product_name} Zaman Serisi")
    plt.xlabel("Tarih")
    plt.ylabel("TL")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# Örnek kullanım
#plot_product_price("Product 1")

plot_manufacturer_product_prices("Man 26", "Product 1")
