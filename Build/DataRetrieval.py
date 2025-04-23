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
        documents = collection.find({}, {"_id": 0}).sort("Date", -1).limit(90)

        for doc in documents:
            if manufacturer_name + " Products" in doc.keys():
                shop_candidates.append(collection_name)
                break  # Bir kere bulduysa yeter, diğer belgeleri taramasın

    return shop_candidates

def fetch_price_data_from_shop(shop_name: str, manufacturer_name: str, start_date: str, end_date: str):
    """
    Fetches product prices between dates from a specific shop collection,
    only for the specified manufacturer's products (e.g., only 'ELectronicMan Products').
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

        # DİKKAT: Sadece doğru manufacturer'ın ürünlerini oku
        manufacturer_products_field = f"{manufacturer_name} Products"

        if manufacturer_products_field in doc:
            products = doc[manufacturer_products_field]
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
    if common_dates.empty:
        return pd.Series(dtype=float)

    profit_series = ((shop_avg[common_dates] / manu_avg[common_dates]) - 1) * 100
    return profit_series

def find_profit_change_dates(shop_df: pd.DataFrame, manufacturer_df: pd.DataFrame, threshold: float = 0.5) -> list:
    """
    Bir shop'ın, üretici fiyatlarına göre kâr yüzdesindeki anlamlı değişim tarihlerini tespit eder.

    Args:
        shop_df (pd.DataFrame): Shop verisi, ['date', 'price'] kolonlarını içermelidir.
        manufacturer_df (pd.DataFrame): Üretici verisi, ['date', 'price'] kolonlarını içermelidir.
        threshold (float): Yüzdelik değişim için eşik değeri (varsayılan %2).

    Returns:
        List[Tuple[pd.Timestamp, float]]: (değişim tarihi, değişim yüzdesi) listesi
    """
    # Eğer boş veri varsa direkt çık
    if shop_df.empty or manufacturer_df.empty:
        return []

    # Ortalama fiyatları günlük bazda al
    shop_avg = shop_df.groupby('date')['price'].mean()
    manu_avg = manufacturer_df.groupby('date')['price'].mean()

    # Ortak tarihleri bul
    common_dates = shop_avg.index.intersection(manu_avg.index)
    if len(common_dates) == 0:
        return []

    # Ortak tarihlerdeki fiyatlarla profit yüzdesi hesapla
    profit_series = ((shop_avg[common_dates] / manu_avg[common_dates]) - 1) * 100
    profit_series = profit_series.sort_index()

    # Günlük değişimleri bul
    profit_change = profit_series.diff().fillna(0)

    # Anlamlı değişimlerin olduğu tarihleri filtrele
    significant_changes = []
    for date, change in profit_change.items():
        if abs(change) >= threshold:
            significant_changes.append((date, change))

    return significant_changes

def find_profit_changes_with_magnitude(shop_name, manufacturer_name, start_date, end_date, threshold=1.0):
    shop_df = fetch_price_data_from_shop(shop_name, manufacturer_name, start_date, end_date)
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

def fetch_price_data_all_shops_products():
    """
    Tüm üreticilerin shoplarındaki ürün fiyat verilerini toplar.
    DataFrame döner: shop, product, date, price
    """
    all_data = []

    manufacturers = fetch_all_manufacturers()
    for manufacturer in manufacturers:
        shops = fetch_shops_for_manufacturer(manufacturer)
        for shop in shops:
            shop_data = fetch_price_data_from_shop(shop, manufacturer, "2020-01-01", "2030-01-01")
            if not shop_data.empty:
                for idx, row in shop_data.iterrows():
                    all_data.append({
                        'shop': shop,
                        'product': row['product_name'],
                        'date': pd.to_datetime(row['date']),
                        'price': row['price']
                    })

    df = pd.DataFrame(all_data)
    return df

def fetch_products_for_shop(manufacturer_name, shop_name):
    """
    Verilen mağazaya (koleksiyon) ve üreticiye göre, o üreticiye ait ürün isimlerini döndürür.
    """

    if shop_name not in db.list_collection_names():
        return []

    collection = db[shop_name]

    # Örnek: "CableMan Products" gibi nested bir key olacak şekilde eriş
    manufacturer_key = f"{manufacturer_name} Products"

    products = set()

    for doc in collection.find({manufacturer_key: {"$exists": True}}, {manufacturer_key: 1}):
        prod_block = doc.get(manufacturer_key, {})
        for key, value in prod_block.items():
            if "Product" in key and "Price" not in key:
                products.add(value)

    return list(products)

# start_date = "2025-01-01"
# end_date = "2025-04-20"
# threshold = 1.99  # Yüzde 2 eşik
#
# manufacturers = fetch_all_manufacturers()
#
# for manufacturer in manufacturers:
#     print(f"\n=== Manufacturer: {manufacturer} ===")
#
#     manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)
#     if manufacturer_df.empty:
#         print(f"{manufacturer} için üretici verisi bulunamadı. Atlanıyor.")
#         continue
#
#     shop_list = fetch_shops_for_manufacturer(manufacturer)
#     print(f"Shoplar: {shop_list}")
#
#     for shop in shop_list:
#         print(f"\n--- Shop: {shop} ---")
#
#         shop_df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
#         if shop_df.empty:
#             print(f"{shop} için veri bulunamadı. Atlanıyor.")
#             continue
#
#         # --- Profit Hesaplama ---
#         profit_series = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
#         if profit_series.empty:
#             print(f"{shop} için profit serisi oluşturulamadı.")
#             continue
#
#         print(f"Profit Serisi (ilk 5 satır):\n{profit_series.head()}")
#
#         # --- Değişim Tarihleri ---
#         changes = find_profit_change_dates(shop_df, manufacturer_df, threshold=threshold)
#
#         if not changes:
#             print("\n✅ Profit yüzdesi sabit, değişim yok.")
#         else:
#             print("\n⚠️ Değişim tespit edildi:")
#             for date, change in changes:
#                 change_type = "artış" if change > 0 else "azalış"
#                 print(f"Date: {date.strftime('%Y-%m-%d')}, {change_type}, Change: {change:.2f}%")
#
#
#



