import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from DataRetrieval import fetch_price_data_from_shop, fetch_manufacturer_data

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

def create_shop_features(shop_list: list, manufacturer: str, start_date: str, end_date: str, max_delay_days=7):
    """
    Shop'lar arasında cosine similarity, ortalama profit farkı ve gecikme ile feature set oluşturur.
    """
    manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)
    if manufacturer_df.empty:
        print(f"{manufacturer} için üretici verisi bulunamadı.")
        return None, None

    shop_profits = {}
    for shop in shop_list:
        shop_df = fetch_price_data_from_shop(shop, start_date, end_date)
        if shop_df.empty:
            print(f"No data found for shop {shop}.")
            continue

        profits = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
        if not profits.empty:
            shop_profits[shop] = profits

    if len(shop_profits) < 2:
        print("Yeterli shop verisi bulunamadı.")
        return None, None

    # Feature üretimi
    X = []
    y = []
    shops = list(shop_profits.keys())

    for i in range(len(shops)):
        for j in range(i + 1, len(shops)):
            series_i = shop_profits[shops[i]].reindex_like(shop_profits[shops[j]]).fillna(0)
            series_j = shop_profits[shops[j]].fillna(0)

            series_i = series_i.values.astype(float)
            series_j = series_j.values.astype(float)

            if len(series_i) == 0 or len(series_j) == 0:
                continue

            similarity = cosine_similarity(series_i.reshape(1, -1), series_j.reshape(1, -1))[0][0]
            profit_diff_mean = np.mean(np.abs(series_i - series_j))
            lag = np.argmax(np.correlate(series_j, series_i, mode='full')) - (len(series_i) - 1)

            X.append([similarity, profit_diff_mean, lag])

            label = 1 if similarity > 0.9 and profit_diff_mean < 6 and abs(lag) <= max_delay_days else 0
            y.append(label)

    return np.array(X), np.array(y)

def detect_leader_follower(shop_profits, date_index, max_day_difference=10):
    shops = list(shop_profits.keys())
    relations = []

    for i in range(len(shops)):
        for j in range(i + 1, len(shops)):
            series_i = shop_profits[shops[i]].fillna(0).values
            series_j = shop_profits[shops[j]].fillna(0).values

            if len(series_i) != len(series_j) or len(series_i) == 0:
                continue

            lag = np.argmax(np.correlate(series_j, series_i, mode='full')) - (len(series_i) - 1)

            if lag > 0:
                leader = shops[i]
                follower = shops[j]
            elif lag < 0:
                leader = shops[j]
                follower = shops[i]
                lag = -lag
            else:
                # lag = 0 ise price değişimi incele
                price_diff_i = np.abs(np.diff(shop_profits[shops[i]].fillna(0).values))
                price_diff_j = np.abs(np.diff(shop_profits[shops[j]].fillna(0).values))

                first_change_i = np.where(price_diff_i > 0)[0]
                first_change_j = np.where(price_diff_j > 0)[0]

                if len(first_change_i) > 0 and len(first_change_j) > 0:
                    change_day_i = first_change_i[0]
                    change_day_j = first_change_j[0]

                    day_difference = abs(change_day_i - change_day_j)

                    if day_difference <= max_day_difference:
                        if change_day_i < change_day_j:
                            leader = shops[i]
                            follower = shops[j]
                            lag = change_day_j - change_day_i
                        elif change_day_j < change_day_i:
                            leader = shops[j]
                            follower = shops[i]
                            lag = change_day_i - change_day_j
                        else:
                            leader = shops[i]
                            follower = shops[j]
                            lag = 0
                    else:
                        leader = shops[i]
                        follower = shops[j]
                        lag = 0  # çok geç değişmiş, simultane kabul
                else:
                    leader = shops[i]
                    follower = shops[j]
                    lag = 0

            # --- Tarih hesaplama
            if len(date_index) > 0:
                try:
                    leader_start = date_index[0]
                    follower_start = leader_start + pd.Timedelta(days=lag)
                except:
                    leader_start = None
                    follower_start = None
            else:
                leader_start = None
                follower_start = None

            relations.append((leader, follower, lag, leader_start, follower_start))

    return relations

def detect_real_leader_follower(change_dates_dict, max_day_difference=10):
    """
    Her değişim dalgası için leader-follower ilişkilerini tespit eder.

    Parametreler:
    - change_dates_dict: {shop_name: [timestamp1, timestamp2, ...]} şeklinde değişim günleri
    - max_day_difference: Lider ile takipçi arasındaki maksimum gün farkı

    Döndürür:
    - relations: (leader, follower, leader_date, follower_date) listesi
    """
    relations = []

    # Bütün değişim tarihlerini birleştir
    all_change_dates = []
    for dates in change_dates_dict.values():
        all_change_dates.extend(dates)

    # Tekrar edenleri sil, sırala
    unique_change_dates = sorted(set(all_change_dates))

    for change_date in unique_change_dates:
        # Bu change_date için kimler değişmiş, onu bul
        changes_on_date = []
        for shop, dates in change_dates_dict.items():
            for d in dates:
                if abs((d - change_date).days) <= max_day_difference:
                    changes_on_date.append((shop, d))

        # Eğer en az 2 kişi değiştiyse, ilişki kur
        if len(changes_on_date) >= 2:
            # En erken değişim yapanı bul
            changes_on_date.sort(key=lambda x: x[1])  # tarihe göre sırala
            leader_shop, leader_date = changes_on_date[0]

            for follower_shop, follower_date in changes_on_date[1:]:
                if leader_shop != follower_shop:
                    relations.append((leader_shop, follower_shop, leader_date, follower_date))

    return relations




# change_dates_dict = {
#     "YourElectrician": [pd.Timestamp('2025-02-19'), pd.Timestamp('2025-03-19')],
#     "MyElectrician": [pd.Timestamp('2025-02-23'), pd.Timestamp('2025-03-22')],
#     "HisElectrician": [pd.Timestamp('2025-02-23'), pd.Timestamp('2025-03-22')]
# }
#
# # Fonksiyonu çağır
# relations = detect_real_leader_follower(change_dates_dict, max_day_difference=10)
#
# # Sonuçları yazdır
# print("\n=== Leader-Follower İlişkileri ===")
# for leader, follower, leader_date, follower_date in relations:
#     print(f"{follower} follows {leader} (Leader Date: {leader_date.date()}, Follower Date: {follower_date.date()})")
#
# # Genel lider özeti çıkar
# leader_summary = {}
# for leader, follower, _, _ in relations:
#     if leader not in leader_summary:
#         leader_summary[leader] = []
#     leader_summary[leader].append(follower)
#
# print("\n=== Genel Lider- Takipçiler Özeti ===")
# for leader, followers in leader_summary.items():
#     unique_followers = list(set(followers))  # Tekrarlamaları kaldır
#     print(f"Leader -> {leader} | Followers -> {', '.join(unique_followers)}")