import pymongo
import pandas as pd
from datetime import datetime

# MongoDB connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["Final_Project"]


# collection_names = db.list_collection_names()
#
# for collection_name in collection_names:
#     collection = db[collection_name]
#     document = collection.find_one()
#     if document:
#         print(f"Collection: {collection_name}")
#         print("Sample Document:")
#         print(document)

def fetch_price_data(start_date: str, end_date: str):
    """
    Fetches product prices or costs between dates from all collections.

    Args:
    - start_date (str): "YYYY-MM-DD"
    - end_date (str): "YYYY-MM-DD"

    Returns:
    - pd.DataFrame: ['shop_id', 'product_name', 'date', 'price']
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    all_data = []
    collection_names = db.list_collection_names()

    for collection_name in collection_names:
        collection = db[collection_name]
        documents = list(collection.find({
            "Date": {"$gte": start, "$lte": end}
        }))

        for doc in documents:
            base_date = doc.get("Date", None)
            if base_date is None:
                continue

            # 1. If 'Cost' exists, treat as a single product
            if "Cost" in doc:
                price_str = doc["Cost"].replace(" TL", "").replace(",", "")
                price = float(price_str)
                all_data.append({
                    "shop_id": collection_name,
                    "product_name": doc.get("Description", "Unknown"),
                    "date": base_date,
                    "price": price
                })

            # 2. If multiple 'Product X' prices exist
            for i in range(1, 30):  # Assume max 30 products
                product_key = f"Product {i}"
                price_key = f"Product {i} Price"
                if product_key in doc and price_key in doc:
                    product_name = doc[product_key]
                    price_str = doc[price_key].replace(" TL", "").replace(",", "")
                    price = float(price_str)
                    all_data.append({
                        "shop_id": collection_name,
                        "product_name": product_name,
                        "date": base_date,
                        "price": price
                    })

    if all_data:
        final_df = pd.DataFrame(all_data)
        final_df['date'] = pd.to_datetime(final_df['date'])
        return final_df
    else:
        print(f"No data found between {start_date} and {end_date}.")
        return pd.DataFrame(columns=['shop_id', 'product_name', 'date', 'price'])


def calculate_daily_percentage_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the daily percentage price change for each shop and product.

    Args:
    - df (pd.DataFrame): Must have ['shop_id', 'product_name', 'date', 'price']

    Returns:
    - pd.DataFrame: ['shop_id', 'product_name', 'date', 'price', 'daily_change']
    """
    if df.empty:
        print("Input dataframe is empty!")
        return df

    # Sort the dataframe by shop_id, product_name and date
    df = df.sort_values(by=['shop_id', 'product_name', 'date'])

    # Calculate daily % change within each shop_id and product_name group
    df['daily_change'] = df.groupby(['shop_id', 'product_name'])['price'].pct_change()

    # Fill NaN changes (first entries) with 0
    df['daily_change'] = df['daily_change'].fillna(0)

    return df


def fetch_price_data_from_collection(collection_name: str, start_date: str, end_date: str):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    collection = db[collection_name]
    documents = list(collection.find({
        "Date": {"$gte": start, "$lte": end}
    }))

    all_data = []

    for doc in documents:
        base_date = doc.get("Date", None)
        if base_date is None:
            continue

        # Eğer 'Cost' yoksa sadece Product'lara bakalım
        for i in range(1, 30):
            prod_key = f"Product {i}"
            price_key = f"Product {i} Price"
            if prod_key in doc and price_key in doc:
                product_name = doc[prod_key]
                price_str = doc[price_key].replace(" TL", "").replace(",", "")
                price = float(price_str)
                all_data.append({
                    "shop_id": collection_name,
                    "product_name": product_name,
                    "date": base_date,
                    "price": price
                })

    if all_data:
        final_df = pd.DataFrame(all_data)
        final_df['date'] = pd.to_datetime(final_df['date'])
        return final_df
    else:
        print(f"No data found for collection {collection_name} between {start_date} and {end_date}.")
        return pd.DataFrame(columns=['shop_id', 'product_name', 'date', 'price'])



def fetch_manufacturer_data(collection_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Belirtilen manufacturer collection'ından ürün fiyatlarını getirir.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    collection = db[collection_name]
    documents = list(collection.find({
        "Date": {"$gte": start, "$lte": end}
    }))

    all_data = []
    for doc in documents:
        base_date = doc.get("Date", None)
        if base_date is None:
            continue

        for i in range(1, 30):
            product_key = f"Product {i}"
            price_key = f"Product {i} Price"
            if product_key in doc and price_key in doc:
                product_name = doc[product_key]
                price_str = doc[price_key].replace(" TL", "").replace(",", "")
                price = float(price_str)
                all_data.append({
                    "shop_id": collection_name,
                    "product_name": product_name,
                    "date": base_date,
                    "price": price
                })

    if all_data:
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        return df
    else:
        print(f"No data found for manufacturer {collection_name} between {start_date} and {end_date}.")
        return pd.DataFrame(columns=['shop_id', 'product_name', 'date', 'price'])


def fetch_shop_data(collection_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Belirtilen shop collection'ından ürün fiyatlarını getirir (ELectronicMan Products + HomeELectricMan Products).
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    collection = db[collection_name]
    documents = list(collection.find({
        "Date": {"$gte": start, "$lte": end}
    }))

    all_data = []
    for doc in documents:
        base_date = doc.get("Date", None)
        if base_date is None:
            continue

        if "ELectronicMan Products" in doc:
            products = doc["ELectronicMan Products"]
            for i in range(1, 30):
                prod_key = f"Product {i}"
                price_key = f"Product {i} Price"
                if prod_key in products and price_key in products:
                    product_name = products[prod_key]
                    price_str = products[price_key].replace(" TL", "").replace(",", "")
                    price = float(price_str)
                    all_data.append({
                        "shop_id": collection_name,
                        "product_name": product_name,
                        "date": base_date,
                        "price": price
                    })

        if "HomeELectricMan Products" in doc:
            products = doc["HomeELectricMan Products"]
            for i in range(1, 30):
                prod_key = f"Product {i}"
                price_key = f"Product {i} Price"
                if prod_key in products and price_key in products:
                    product_name = products[prod_key]
                    price_str = products[price_key].replace(" TL", "").replace(",", "")
                    price = float(price_str)
                    all_data.append({
                        "shop_id": collection_name,
                        "product_name": product_name,
                        "date": base_date,
                        "price": price
                    })

    if all_data:
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        return df
    else:
        print(f"No data found for shop {collection_name} between {start_date} and {end_date}.")
        return pd.DataFrame(columns=['shop_id', 'product_name', 'date', 'price'])


def fetch_all_manufacturers():
    """
    Veritabanındaki manufacturerları (üretici koleksiyonlarını) getirir.
    Şu anda tüm manufacturer'ların ismi ELectronicMan, HomeELectricMan gibi net.
    """
    collection_names = db.list_collection_names()

    # Belirli bir kural var mı? Mesela sonu "Man" ile bitiyor mu?
    # Şu an basit yapalım: İçinde "Man" geçenler manufacturerdır diye alalım
    manufacturers = [name for name in collection_names if "Man" in name]

    return manufacturers


def fetch_shops_for_manufacturer(manufacturer_name):
    collection_names = db.list_collection_names()
    shop_candidates = []

    for collection_name in collection_names:
        if collection_name == manufacturer_name:
            continue

        collection = db[collection_name]
        sample_doc = collection.find_one()
        if not sample_doc:
            continue

        expected_field = manufacturer_name + " Products"
        if expected_field in sample_doc:
            shop_candidates.append(collection_name)

    return shop_candidates



def fetch_price_data_from_shop(shop_name: str, start_date: str, end_date: str):
    """
    Fetches product prices between dates from a specific shop collection.
    Dynamically finds all manufacturer product fields (e.g., ELectronicMan Products, CableMan Products).
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    collection = db[shop_name]
    documents = list(collection.find({
        "Date": {"$gte": start, "$lte": end}
    }))

    all_data = []

    for doc in documents:
        base_date = doc.get("Date", None)
        if base_date is None:
            continue

        # --- Yeni: Her belge içinde "Products" geçen tüm alanları ara
        for key in doc.keys():
            if "Products" in key:
                products = doc[key]
                for i in range(1, 30):
                    prod_key = f"Product {i}"
                    price_key = f"Product {i} Price"
                    if prod_key in products and price_key in products:
                        product_name = products[prod_key]
                        price_str = products[price_key].replace(" TL", "").replace(",", "")
                        price = float(price_str)
                        all_data.append({
                            "shop_id": shop_name,
                            "product_name": product_name,
                            "date": base_date,
                            "price": price
                        })

    if all_data:
        final_df = pd.DataFrame(all_data)
        final_df['date'] = pd.to_datetime(final_df['date'])
        return final_df
    else:
        print(f"No data found for shop {shop_name} between {start_date} and {end_date}.")
        return pd.DataFrame(columns=['shop_id', 'product_name', 'date', 'price'])

def calculate_profit_relative_to_manufacturer(shop_df: pd.DataFrame, manufacturer_df: pd.DataFrame) -> pd.Series:
    """
    Shop fiyatlarının manufacturer fiyatlarına göre profit oranlarını hesaplar.
    """
    shop_avg = shop_df.groupby("date")["price"].mean()
    manu_avg = manufacturer_df.groupby("date")["price"].mean()

    # Ortak tarihler
    common_dates = shop_avg.index.intersection(manu_avg.index)

    profit_series = ((shop_avg[common_dates] / manu_avg[common_dates]) - 1) * 100
    return profit_series

def find_profit_change_dates(shop_df, manufacturer_df, threshold=0.5):
    """
    Bir shop'ın manufacturer'a göre profit değişimlerini tespit eder.

    Parametreler:
    - shop_df: Shop'a ait fiyat verileri (DataFrame: ['date', 'price'])
    - manufacturer_df: Manufacturer fiyat verileri (DataFrame: ['date', 'price'])
    - threshold: Değişim yüzdesi algılamak için minimum değişim eşiği (%)

    Döndürür:
    - List of (değişim tarihi, değişim yüzdesi, artış/azalış)
    """

    # Ortalama fiyatlar
    shop_avg = shop_df.groupby("date")["price"].mean()
    manu_avg = manufacturer_df.groupby("date")["price"].mean()

    # Ortak tarihler
    common_dates = shop_avg.index.intersection(manu_avg.index)

    if len(common_dates) == 0:
        return []

    # Profit yüzdesi hesapla
    profit_series = ((shop_avg[common_dates] / manu_avg[common_dates]) - 1) * 100

    changes = []
    prev_profit = None

    for date, profit in profit_series.items():
        if prev_profit is not None:
            diff = profit - prev_profit
            if abs(diff) >= threshold:  # Eşik değerinden büyük değişim varsa
                direction = "artış" if diff > 0 else "azalış"
                changes.append((date, diff, direction))
        prev_profit = profit

    return changes


def find_profit_changes_with_magnitude(shop_name, manufacturer_name, start_date, end_date, threshold=1.0):
    shop_df = fetch_price_data_from_shop(shop_name, start_date, end_date)
    manufacturer_df = fetch_manufacturer_data(manufacturer_name, start_date, end_date)

    if shop_df.empty or manufacturer_df.empty:
        return []

    shop_profit = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
    shop_profit = shop_profit.sort_index()

    changes = []
    previous_date = None
    previous_profit = None

    for date, profit in shop_profit.items():
        if previous_profit is not None:
            diff = profit - previous_profit
            if abs(diff) >= threshold:
                change_type = "artış" if diff > 0 else "azalış"
                changes.append((date, diff, change_type))
        previous_profit = profit
        previous_date = date

    return changes



# #
# df_prices = fetch_price_data("2025-01-18", "2025-04-18")
# print(df_prices)
#
#
# df_prices = fetch_price_data("2025-01-18", "2025-04-18")
# df_with_changes = calculate_daily_percentage_change(df_prices)
#
# print(df_with_changes.head())
# print(df_with_changes.shape)
# print(df_with_changes.sample(10))  # Rastgele 10 satır göster
# print(df_with_changes[df_with_changes['daily_change'] != 0].head(10))  # Değişim olan ürünlerden 10 tanesini göster

# # Sadece "ELectronicMan" verisini çekelim:
# df_YourElectrician = fetch_price_data_from_collection("YourElectrician", "2025-01-18", "2025-04-18")
# print(df_YourElectrician.head(50))  # İlk 10 satırı göster
# print(df_YourElectrician.shape)     # Kaç satır veri geldiğini göster
#
#
# collection = db["YourElectrician"]
# sample_doc = collection.find_one()
# print(sample_doc)


# df_manufacturer = fetch_manufacturer_data("ELectronicMan", "2025-01-18", "2025-04-18")
# print(df_manufacturer.head())
# print(df_manufacturer.shape)
#
#
# for shop in ["YourElectrician", "MyElectrician", "HisElectrician"]:
#     df_shop = fetch_shop_data(shop, "2025-01-18", "2025-04-18")
#     print(f"{shop} - {df_shop.shape}")

# manufacturers = fetch_all_manufacturers()
# print("Manufacturers:", manufacturers)
#
# for manu in manufacturers:
#     shops = fetch_shops_for_manufacturer(manu)
#     print(f"{manu} için shops:", shops)

# df_your_shop = fetch_price_data_from_shop("YourElectrician", "2025-01-18", "2025-04-18")
# print(df_your_shop.head())
# print(df_your_shop.shape)
#
# df_migros = fetch_price_data_from_shop("MIGROS", "2025-01-01", "2025-05-01")
# print(df_migros.shape)
# print(df_migros.head())

# change_dates = find_profit_changes_with_magnitude(
#     shop_name="YourElectrician",
#     manufacturer_name="ELectronicMan",
#     start_date="2025-01-23",
#     end_date="2025-04-18"
# )
#
# print("Profit değişimi olan tarihler:", change_dates)
#
# change_dates = find_profit_changes_with_magnitude(
#     shop_name="MyElectrician",
#     manufacturer_name="ELectronicMan",
#     start_date="2025-01-23",
#     end_date="2025-04-18"
# )
#
# print("Profit değişimi olan tarihler:", change_dates)
#
# change_dates = find_profit_changes_with_magnitude(
#     shop_name="HisElectrician",
#     manufacturer_name="ELectronicMan",
#     start_date="2025-01-23",
#     end_date="2025-04-18"
# )
#
# print("Profit değişimi olan tarihler:", change_dates)