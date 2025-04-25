import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from DataRetrieval import fetch_manufacturer_data, fetch_shop_data
from datetime import timedelta

def generate_manufacturer_features(manufacturer: str, shop_list: list, start_date: str, end_date: str,
                                   profit_threshold=0.5, delay_tolerance=7):
    """
    Manufacturer bazlı feature engineering:
    - Her fiyat artışından sonra mağazaların nasıl tepki verdiğini inceler.
    - Feature: profit difference, delay
    - Label: collusion (1) / not collusion (0)
    """

    # 1. Manufacturer verisini çekelim
    df_manufacturer = fetch_manufacturer_data(manufacturer, start_date, end_date)

    if df_manufacturer.empty:
        print(f"No data for manufacturer {manufacturer}.")
        return None, None

    # 2. Tarihleri düzenleyelim
    df_manufacturer["date"] = pd.to_datetime(df_manufacturer["date"])
    df_manufacturer.sort_values(["product_name", "date"], inplace=True)

    # 3. Günlük ortalama fiyatları bulalım
    daily_avg = df_manufacturer.groupby("date")["price"].mean().sort_index()

    # 4. Manufacturer fiyat artış günlerini bul (profit_threshold üstü artışlarda)
    price_diff = daily_avg.pct_change()
    increase_days = price_diff[price_diff > profit_threshold / 100].index.tolist()

    features = []
    labels = []

    # 5. Her artış günü için shop hareketlerini inceleyelim
    for change_day in increase_days:
        feature_row = []

        # Her shop için o günden sonraki delay ve profit artışı kontrolü
        for shop in shop_list:
            shop_df = fetch_shop_data(shop, start_date, end_date)
            if shop_df.empty:
                continue

            shop_df["date"] = pd.to_datetime(shop_df["date"])
            shop_df.sort_values(["product_name", "date"], inplace=True)

            # O gün ve takip eden günlerde fiyat hareketi
            profit_series = []

            for date_offset in range(delay_tolerance + 1):
                check_date = change_day + timedelta(days=date_offset)
                day_data = shop_df[shop_df["date"] == check_date]

                if not day_data.empty:
                    avg_price = day_data["price"].mean()
                    manufacturer_price = daily_avg.get(check_date, None)

                    if manufacturer_price is not None:
                        profit = ((avg_price / manufacturer_price) - 1) * 100
                        profit_series.append((date_offset, profit))

            # Feature engineering: ilk artış günü ve gecikme
            if profit_series:
                first_increase = profit_series[0][1]  # İlk gün profiti
                delay = profit_series[0][0]  # Kaç gün sonra arttı
            else:
                first_increase = 0
                delay = delay_tolerance + 1

            feature_row.append(first_increase)
            feature_row.append(delay)

        # Eğer en az bir mağaza için feature oluştuysa ekleyelim
        if feature_row:
            features.append(feature_row)

            # --- Label oluşturma (örnek: en az 2 mağaza aynı anda artış yaparsa collusion var)
            colluding_shops = [delay for idx, delay in enumerate(feature_row[1::2]) if delay <= 2]
            label = 1 if len(colluding_shops) >= 2 else 0
            labels.append(label)

    return np.array(features), np.array(labels)

def generate_manufacturer_features_ML(manufacturer: str, shop_list: list, start_date: str, end_date: str,
                                      profit_threshold=0.5, delay_tolerance=7):
    """
    Gelişmiş feature engineering fonksiyonu.
    """
    df_manufacturer = fetch_manufacturer_data(manufacturer, start_date, end_date)
    if df_manufacturer.empty:
        print(f"No data for manufacturer {manufacturer}.")
        return None, None

    df_manufacturer["date"] = pd.to_datetime(df_manufacturer["date"])
    df_manufacturer.sort_values(["product_name", "date"], inplace=True)
    daily_avg = df_manufacturer.groupby("date")["price"].mean().sort_index()
    price_diff = daily_avg.pct_change()
    increase_days = price_diff[price_diff > profit_threshold / 100].index.tolist()

    all_features = []
    all_labels = []

    for change_day in increase_days:
        feature_row = []
        delays = []
        profit_trends = []

        for shop in shop_list:
            shop_df = fetch_shop_data(shop, start_date, end_date)
            if shop_df.empty:
                feature_row += [0, delay_tolerance + 1, 0]  # dummy values
                continue

            shop_df["date"] = pd.to_datetime(shop_df["date"])
            shop_df.sort_values(["product_name", "date"], inplace=True)

            profit_series = []
            for date_offset in range(delay_tolerance + 1):
                check_date = change_day + timedelta(days=date_offset)
                shop_price = shop_df[shop_df["date"] == check_date]["price"].mean()
                manu_price = daily_avg.get(check_date, None)

                if pd.notna(shop_price) and pd.notna(manu_price):
                    profit = ((shop_price / manu_price) - 1) * 100
                    profit_series.append((date_offset, profit))

            if profit_series:
                first_delay = profit_series[0][0]
                first_profit = profit_series[0][1]
                profit_std = np.std([p[1] for p in profit_series])
            else:
                first_delay = delay_tolerance + 1
                first_profit = 0
                profit_std = 0

            feature_row += [first_profit, first_delay, profit_std]
            delays.append(first_delay)
            profit_trends.append([p[1] for p in profit_series])

        # Basit label: En az 2 mağaza delay <= 2 gün içinde tepki verirse collusion
        short_delays = [d for d in delays if d <= 2]
        label = 1 if len(short_delays) >= 2 else 0

        all_features.append(feature_row)
        all_labels.append(label)

    return np.array(all_features), np.array(all_labels)
