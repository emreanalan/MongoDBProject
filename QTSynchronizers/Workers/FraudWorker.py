from PySide6.QtCore import QObject, Signal
from datetime import timedelta
import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from DataRetrieval import (
    fetch_all_manufacturers,
    fetch_shops_for_manufacturer,
    fetch_price_data_from_shop,
    fetch_manufacturer_data,
    fetch_price_data_all_shops_products,
)
from tabulate import tabulate

class MLFraudWorker(QObject):
    newOutput = Signal(str)
    finished = Signal()

    def __init__(self, start_date, end_date):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date

    def run(self):
        self.newOutput.emit("=== STARTING MACHINE LEARNING FRAUD DETECTION ===\n")
        data = fetch_price_data_all_shops_products()
        X = data[['price']]
        model = IsolationForest(contamination=0.05, random_state=42)
        data['anomaly'] = model.fit_predict(X)

        fraud_data = data[data['anomaly'] == -1]
        grouped = fraud_data.groupby(['shop', 'product'])

        fraud_rows = []

        for (shop, product), group in grouped:
            group = group.sort_values(by='date')
            dates = group['date'].tolist()
            prices = group['price'].tolist()

            temp_dates, temp_prices, prev_date = [], [], None
            for d, p in zip(dates, prices):
                if not prev_date or (pd.to_datetime(d) - pd.to_datetime(prev_date)).days == 1:
                    temp_dates.append(d)
                    temp_prices.append(p)
                else:
                    if len(temp_dates) >= 1:
                        price_change = (temp_prices[-1] - temp_prices[0]) / temp_prices[0] * 100
                        if abs(price_change) >= 3:
                            fraud_rows.append([
                                shop,
                                product,
                                temp_dates[0].strftime('%Y-%m-%d'),
                                temp_dates[-1].strftime('%Y-%m-%d'),
                                f"{temp_prices[0]:,.2f} TL",
                                f"{temp_prices[-1]:,.2f} TL",
                                f"{price_change:+.2f}%"
                            ])
                    temp_dates, temp_prices = [d], [p]
                prev_date = d

            if len(temp_dates) >= 1:
                price_change = (temp_prices[-1] - temp_prices[0]) / temp_prices[0] * 100
                if abs(price_change) >= 3:
                    fraud_rows.append([
                        shop,
                        product,
                        temp_dates[0].strftime('%Y-%m-%d'),
                        temp_dates[-1].strftime('%Y-%m-%d'),
                        f"{temp_prices[0]:,.2f} TL",
                        f"{temp_prices[-1]:,.2f} TL",
                        f"{price_change:+.2f}%"
                    ])

        if fraud_rows:
            self.newOutput.emit("\n⚠️ Suspicious Price Changes Detected!\n")
            headers = ["Shop", "Product", "Start Date", "End Date", "Start Price", "End Price", "Change %"]
            table = tabulate(fraud_rows, headers=headers, tablefmt="pretty")
            self.newOutput.emit(table)

            self.newOutput.emit("\n=== SUMMARY REPORT ===\n")
            shop_summary = defaultdict(list)
            for row in fraud_rows:
                shop_summary[row[0]].append(row[1])

            for shop, products in shop_summary.items():
                total_products = len(set(products))
                most_changed_product = max(set(products), key=products.count)
                self.newOutput.emit(f"Shop: {shop} | Toplam Şüpheli Ürün: {total_products} | En Çok Değişen Ürün: {most_changed_product}")
        else:
            self.newOutput.emit("\n✅ No suspicious price behavior detected.")

        self.newOutput.emit("\n=== MACHINE LEARNING FRAUD DETECTION COMPLETED ===\n")
        self.finished.emit()


class RuleFraudWorker(QObject):
    newOutput = Signal(str)
    finished = Signal()

    def __init__(self, start_date, end_date, max_profit_threshold):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.max_profit_threshold = max_profit_threshold  # PRICE_DIFF_THRESHOLD olarak kullanılacak

    def run(self):
        PRICE_DIFF_THRESHOLD = float(self.max_profit_threshold)
        PRICE_CHANGE_THRESHOLD = 1.99
        start = pd.to_datetime(self.start_date)
        end = pd.to_datetime(self.end_date)

        self.newOutput.emit("\n=== FULL AUTOMATED FRAUD DETECTION REPORT ===\n")
        manufacturers = fetch_all_manufacturers()

        for manufacturer in manufacturers:
            self.newOutput.emit(f"\n=== Manufacturer: {manufacturer} ===\n")
            shop_list = fetch_shops_for_manufacturer(manufacturer)
            if not shop_list:
                continue

            self.newOutput.emit(f"Shoplar: {shop_list}\n")
            manufacturer_df = fetch_manufacturer_data(manufacturer, self.start_date, self.end_date)
            if manufacturer_df.empty:
                continue

            all_products = manufacturer_df['product_name'].unique()

            # Shop bazlı cache'leme
            shop_data_cache = {
                shop: fetch_price_data_from_shop(shop, manufacturer, self.start_date, self.end_date)
                for shop in shop_list
            }

            for shop, shop_df in shop_data_cache.items():
                if shop_df.empty:
                    continue

                for product in all_products:
                    shop_product_data = shop_df[shop_df['product_name'] == product]
                    if shop_product_data.empty:
                        continue

                    shop_prices = shop_product_data[['date', 'price']].set_index('date').sort_index()
                    if shop_prices.empty or len(shop_prices) < 2:
                        continue

                    price_diff = shop_prices['price'].diff().fillna(0)
                    price_change_percentage = (price_diff / shop_prices['price'].shift(1)).fillna(0) * 100
                    significant_changes = price_change_percentage[abs(price_change_percentage) >= PRICE_CHANGE_THRESHOLD].index
                    if len(significant_changes) == 0:
                        continue

                    start_date = significant_changes[0]
                    end_date = significant_changes[1] if len(significant_changes) > 1 else shop_prices.index[-1]
                    middle_date = start_date + timedelta(days=(end_date - start_date).days // 2)

                    all_prices = []
                    for s, s_df in shop_data_cache.items():
                        s_prod = s_df[(s_df['product_name'] == product) & (s_df['date'] == middle_date)]
                        if not s_prod.empty:
                            all_prices.append(s_prod['price'].values[0])

                    if not all_prices:
                        continue

                    avg_price = np.mean(all_prices)
                    fraud_price_data = shop_df[(shop_df['product_name'] == product) & (shop_df['date'] == middle_date)]
                    if fraud_price_data.empty:
                        continue

                    fraud_price = fraud_price_data['price'].values[0]
                    price_diff = abs((fraud_price - avg_price) / avg_price) * 100

                    if price_diff >= PRICE_DIFF_THRESHOLD:
                        self.newOutput.emit(f"⚠️ Şüpheli fiyat tespit edildi:\n- Shop: {shop}\n  - Start Date: {start_date.date()} / End Date: {end_date.date()}\n    Normal Product [{product}] Price: {avg_price:.2f} TL --> Fraud Product [{product}] Price: {fraud_price:.2f} TL")

        self.newOutput.emit("\n=== COMPLETED FULL FRAUD REPORT ===\n")
        self.finished.emit()