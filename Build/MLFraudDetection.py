import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from DataRetrieval import fetch_price_data_all_shops_products
from tabulate import tabulate

# === Parametreler ===
PRICE_CHANGE_THRESHOLD_PERCENT = 3  # %3 ve üstü değişim varsa listele
GROUP_CONSECUTIVE_DAYS = True  # Art arda günleri gruplama açıldı

# === Veri çekme ===
def fetch_all_price_data():
    return fetch_price_data_all_shops_products()

# === Ana İşlem ===
print("=== STARTING MACHINE LEARNING FRAUD DETECTION ===\n")

data = fetch_all_price_data()

# Özellik çıkarımı
X = data[['price']]
model = IsolationForest(contamination=0.05, random_state=42)
data['anomaly'] = model.fit_predict(X)

# Sadece anomalileri filtrele
fraud_data = data[data['anomaly'] == -1]

# Shop ve Product bazlı grupla
grouped = fraud_data.groupby(['shop', 'product'])

summary_report = []
full_output = []

for (shop, product), group in grouped:
    group = group.sort_values(by='date')
    dates = group['date'].tolist()
    prices = group['price'].tolist()

    # Art arda günleri grupla
    temp_dates = []
    temp_prices = []
    prev_date = None
    prev_price = None

    for d, p in zip(dates, prices):
        if not prev_date:
            temp_dates.append(d)
            temp_prices.append(p)
        else:
            # İki gün art arda mı?
            if (pd.to_datetime(d) - pd.to_datetime(prev_date)).days == 1:
                temp_dates.append(d)
                temp_prices.append(p)
            else:
                # Araya gün girmişse önceki grubu yazdır
                if len(temp_dates) >= 1:
                    price_change = (temp_prices[-1] - temp_prices[0]) / temp_prices[0] * 100
                    if abs(price_change) >= PRICE_CHANGE_THRESHOLD_PERCENT:
                        full_output.append(f"Shop: {shop} | Product: {product} | Dates: {temp_dates[0]} → {temp_dates[-1]} | Prices: {temp_prices[0]} TL → {temp_prices[-1]} TL")
                temp_dates = [d]
                temp_prices = [p]
        prev_date = d
        prev_price = p

    # Son grubu da yazdır
    if len(temp_dates) >= 1:
        price_change = (temp_prices[-1] - temp_prices[0]) / temp_prices[0] * 100
        if abs(price_change) >= PRICE_CHANGE_THRESHOLD_PERCENT:
            full_output.append(f"Shop: {shop} | Product: {product} | Dates: {temp_dates[0]} → {temp_dates[-1]} | Prices: {temp_prices[0]} TL → {temp_prices[-1]} TL")

    summary_report.append((shop, product, len(group)))

# === Çıktı Yazdır ===
# === Yeni Tablo Tipi Çıktı ===


# full_output'dan tablo için veri listesi oluştur
fraud_rows = []

for (shop, product), group in grouped:
    group = group.sort_values(by='date')
    dates = group['date'].tolist()
    prices = group['price'].tolist()

    temp_dates = []
    temp_prices = []
    prev_date = None

    for d, p in zip(dates, prices):
        if not prev_date:
            temp_dates.append(d)
            temp_prices.append(p)
        else:
            if (pd.to_datetime(d) - pd.to_datetime(prev_date)).days == 1:
                temp_dates.append(d)
                temp_prices.append(p)
            else:
                if len(temp_dates) >= 1:
                    price_change = (temp_prices[-1] - temp_prices[0]) / temp_prices[0] * 100
                    if abs(price_change) >= PRICE_CHANGE_THRESHOLD_PERCENT:
                        fraud_rows.append([
                            shop,
                            product,
                            temp_dates[0].strftime('%Y-%m-%d'),
                            temp_dates[-1].strftime('%Y-%m-%d'),
                            f"{temp_prices[0]:,.2f} TL",
                            f"{temp_prices[-1]:,.2f} TL",
                            f"{price_change:+.2f}%"
                        ])
                temp_dates = [d]
                temp_prices = [p]
        prev_date = d

    if len(temp_dates) >= 1:
        price_change = (temp_prices[-1] - temp_prices[0]) / temp_prices[0] * 100
        if abs(price_change) >= PRICE_CHANGE_THRESHOLD_PERCENT:
            fraud_rows.append([
                shop,
                product,
                temp_dates[0].strftime('%Y-%m-%d'),
                temp_dates[-1].strftime('%Y-%m-%d'),
                f"{temp_prices[0]:,.2f} TL",
                f"{temp_prices[-1]:,.2f} TL",
                f"{price_change:+.2f}%"
            ])

# Tabloyu yazdır
if fraud_rows:
    print("\n⚠️ \033[91mSuspicious Price Changes Detected!\033[0m\n")
    headers = ["Shop", "Product", "Start Date", "End Date", "Start Price", "End Price", "Change %"]
    print(tabulate(fraud_rows, headers=headers, tablefmt="pretty"))

    print("\n=== SUMMARY REPORT ===\n")
    shop_summary = defaultdict(list)
    for row in fraud_rows:
        shop_summary[row[0]].append(row[1])

    for shop, products in shop_summary.items():
        total_products = len(set(products))
        most_changed_product = max(set(products), key=products.count)
        print(f"Shop: {shop} | Toplam Şüpheli Ürün: {total_products} | En Çok Değişen Ürün: {most_changed_product}")

else:
    print("\n✅ No suspicious price behavior detected.")

print("\n=== MACHINE LEARNING FRAUD DETECTION COMPLETED ===")

