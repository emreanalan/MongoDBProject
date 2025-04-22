# FraudDetector.py

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from DataRetrieval import (
    fetch_all_manufacturers,
    fetch_shops_for_manufacturer,
    fetch_price_data_from_shop,
    fetch_manufacturer_data,
)

PRICE_DIFF_THRESHOLD = 6  # %10 fark varsa şüpheli
PRICE_CHANGE_THRESHOLD = 1.99  # %2 değişim varsa tarih değişimi kabul edilecek
START_DATE = "2025-01-01"
END_DATE = "2025-04-20"

def find_middle_date(start_date, end_date):
    delta = end_date - start_date
    middle_date = start_date + timedelta(days=delta.days // 2)
    return middle_date

def percentage_difference(base, new):
    if base == 0:
        return 0
    return abs((new - base) / base) * 100

print("\n=== FULL AUTOMATED FRAUD DETECTION REPORT ===\n")

manufacturers = fetch_all_manufacturers()

for manufacturer in manufacturers:
    print(f"\n=== Manufacturer: {manufacturer} ===\n")

    shop_list = fetch_shops_for_manufacturer(manufacturer)
    if not shop_list:
        continue

    print(f"Shoplar: {shop_list}\n")

    manufacturer_df = fetch_manufacturer_data(manufacturer, START_DATE, END_DATE)
    if manufacturer_df.empty:
        continue

    all_products = manufacturer_df['product_name'].unique()

    for shop in shop_list:
        shop_df = fetch_price_data_from_shop(shop, manufacturer, START_DATE, END_DATE)
        if shop_df.empty:
            continue

        detected_frauds = []

        for product in all_products:
            shop_product_data = shop_df[shop_df['product_name'] == product]
            if shop_product_data.empty:
                continue

            shop_prices = shop_product_data[['date', 'price']].set_index('date').sort_index()

            if shop_prices.empty or len(shop_prices) < 2:
                continue

            # Fiyat değişimlerini bul
            price_diff = shop_prices['price'].diff().fillna(0)
            price_change_percentage = (price_diff / shop_prices['price'].shift(1)).fillna(0) * 100

            significant_changes = price_change_percentage[abs(price_change_percentage) >= PRICE_CHANGE_THRESHOLD].index

            if len(significant_changes) == 0:
                continue

            start_date = significant_changes[0]
            end_date = significant_changes[1] if len(significant_changes) > 1 else shop_prices.index[-1]

            middle_date = find_middle_date(start_date, end_date)

            # Normal fiyat: tüm shoplardan alınacak
            all_shops_prices = []

            for s in shop_list:
                s_df = fetch_price_data_from_shop(s, manufacturer, START_DATE, END_DATE)
                if s_df.empty:
                    continue

                s_product_data = s_df[(s_df['product_name'] == product) & (s_df['date'] == middle_date)]
                if not s_product_data.empty:
                    all_shops_prices.append(s_product_data['price'].values[0])

            if not all_shops_prices:
                continue

            avg_normal_price = np.mean(all_shops_prices)

            # Fraud shop middle date fiyatı
            fraud_price_data = shop_df[(shop_df['product_name'] == product) & (shop_df['date'] == middle_date)]
            if fraud_price_data.empty:
                continue

            fraud_price = fraud_price_data['price'].values[0]

            # Fiyat farkı
            price_diff = percentage_difference(avg_normal_price, fraud_price)

            if price_diff >= PRICE_DIFF_THRESHOLD:
                detected_frauds.append((product, avg_normal_price, fraud_price, start_date, end_date))

        if detected_frauds:
            print(f"⚠️ Şüpheli fiyat tespit edildi:")
            print(f"- Shop: {shop}")
            for product, normal_price, fraud_price, start_date, end_date in detected_frauds:
                print(
                    f"  - Start Date: {start_date.date()} / End Date: {end_date.date()}\n"
                    f"    Normal Product [{product}] Price: {normal_price:.2f} TL --> Fraud Product [{product}] Price: {fraud_price:.2f} TL"
                )

print("\n=== COMPLETED FULL FRAUD REPORT ===\n")
