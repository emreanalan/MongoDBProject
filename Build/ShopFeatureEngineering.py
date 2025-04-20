import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from DataRetrieval import (
    fetch_all_manufacturers,
    fetch_shops_for_manufacturer,
    fetch_price_data_from_shop,
    fetch_manufacturer_data,
    find_profit_change_dates,
)

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
        shop_df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
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
    Mağazalar arasında lider-takipçi ilişkisini tespit eder.
    Sadece pozitif gecikmeler (delay > 0) lider-takipçi ilişkisi kabul edilir.
    """
    relationships = []

    shops = list(change_dates_dict.keys())

    for i in range(len(shops)):
        leader_shop = shops[i]
        leader_changes = change_dates_dict[leader_shop]

        for leader_date in leader_changes:
            for j in range(len(shops)):
                if i == j:
                    continue  # Kendisiyle karşılaştırma yapma

                follower_shop = shops[j]
                follower_changes = change_dates_dict[follower_shop]

                for follower_date in follower_changes:
                    delay = (follower_date - leader_date).days

                    # 🔥 Burada kritik değişiklik yaptık:
                    if 0 < delay <= max_day_difference:
                        relationships.append((leader_shop, follower_shop, leader_date, follower_date))
                        break  # Bir eşleşme bulunca diğer lider tarihine geç

    return relationships

def detect_simultaneous_shops(shop_profits, similarity_threshold=0.98):
    """
    Aynı anda hareket eden (profit sabit ilerleyen) shopları tespit eder.

    Returns:
    - simultaneous_pairs: (shop1, shop2, date, profit)
    - isolated_shops: (shop, date, profit)
    """
    simultaneous_pairs = []
    isolated_shops = []

    shops = list(shop_profits.keys())

    for i in range(len(shops)):
        shop_i = shops[i]
        profits_i = shop_profits[shop_i]

        if profits_i.empty:
            continue

        found_pair = False

        for j in range(i + 1, len(shops)):
            shop_j = shops[j]
            profits_j = shop_profits[shop_j]

            if profits_j.empty:
                continue

            # Ortalama similarity hesapla
            common_dates = profits_i.index.intersection(profits_j.index)

            if len(common_dates) == 0:
                continue

            diff = (profits_i[common_dates] - profits_j[common_dates]).abs()
            mean_diff = diff.mean()

            if mean_diff <= (1 - similarity_threshold) * 100:  # Örneğin 2% farklılık toleransı
                date = common_dates[0]
                profit = profits_i[date]
                simultaneous_pairs.append((shop_i, shop_j, date, profit))
                found_pair = True

        if not found_pair:
            date = profits_i.index[0]
            profit = profits_i.iloc[0]
            isolated_shops.append((shop_i, date, profit))

    return simultaneous_pairs, isolated_shops

# start_date = "2025-01-01"
# end_date = "2025-04-20"
#
# print("\n=== FULL AUTOMATED LEADER-FOLLOWER DETECTION ===\n")
#
# manufacturers = fetch_all_manufacturers()
#
# for manufacturer in manufacturers:
#     print(f"\n=== Manufacturer: {manufacturer} ===")
#
#     shop_list = fetch_shops_for_manufacturer(manufacturer)
#     if not shop_list:
#         print(f"{manufacturer} için shop bulunamadı. Atlanıyor.")
#         continue
#
#     change_dates_dict = {}
#     shop_profits = {}
#
#     for shop in shop_list:
#         shop_df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
#         manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)
#
#         if shop_df.empty or manufacturer_df.empty:
#             print(f"{shop} için yeterli veri yok. Atlanıyor.")
#             continue
#
#         # Profit serisi
#         profit_series = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
#
#         # Shop profits to be used later for simultaneous detection
#         shop_profits[shop] = profit_series
#
#         # Değişim günlerini bul
#         change_dates = []
#         profit_diff = profit_series.diff().fillna(0)
#
#         for date, diff in profit_diff.items():
#             if abs(diff) >= 1.99:  # Threshold olarak 1.99 kullanıyoruz
#                 change_dates.append(date)
#
#         if change_dates:
#             change_dates_dict[shop] = change_dates
#
#     if not change_dates_dict:
#         print(f"{manufacturer} için değişim tespit edilemedi.")
#     else:
#         print("\nDetected Change Dates:")
#         for shop, dates in change_dates_dict.items():
#             print(f"{shop}: {[d.strftime('%Y-%m-%d') for d in dates]}")
#
#         # Leader-follower ilişkileri
#         relations = detect_real_leader_follower(change_dates_dict, max_day_difference=7)
#
#         if not relations:
#             print("\nNo Leader-Follower relations found.")
#         else:
#             print("\nLeader-Follower Relations:")
#             for leader, follower, leader_date, follower_date in relations:
#                 print(f"{follower} follows {leader} | Leader Change: {leader_date.date()}, Follower Change: {follower_date.date()}")
#
#     ## --- BURADAN SONRA KALAN 2 FONKSİYONUN TESTLERİ BAŞLIYOR ---
#
#     print("\n[Extra Feature Test] Cosine Similarity and Feature Matrix")
#
#     if len(shop_profits) >= 2:
#         # create_shop_features kullanımı
#         X, y = create_shop_features(shop_list, manufacturer, start_date, end_date, max_delay_days=7)
#
#         if X is not None and y is not None:
#             print("Feature Matrix (X):")
#             print(X)
#             print("Labels (y):")
#             print(y)
#         else:
#             print("Feature matrix oluşturulamadı.")
#
#         # detect_simultaneous_shops kullanımı
#         simultaneous_pairs, isolated_shops = detect_simultaneous_shops(shop_profits, similarity_threshold=0.98)
#
#         print("\nSimultaneous Pairs:")
#         for shop1, shop2, date, profit in simultaneous_pairs:
#             print(f"{shop1} & {shop2} simultaneous at {date.date()} with profit: {profit}")
#
#         print("\nIsolated Shops:")
#         for shop, date, profit in isolated_shops:
#             print(f"{shop} isolated at {date.date()} with profit: {profit}")
#
#     else:
#         print("Shop verisi yeterli değil. Feature ve Simultaneous Testler atlandı.")
#
# print("\n=== COMPLETED ALL TESTS ===")

