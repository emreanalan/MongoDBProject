from DataRetrieval import (
    fetch_all_manufacturers,
    fetch_shops_for_manufacturer,
    fetch_price_data_from_shop,
    fetch_manufacturer_data,
    find_profit_change_dates,
)
from ShopFeatureEngineering import (
    detect_real_leader_follower,
    calculate_profit_relative_to_manufacturer,
    create_shop_features,
    detect_simultaneous_shops
)
import pandas as pd

start_date = "2025-01-01"
end_date = "2025-04-20"

print("\n=== FULL AUTOMATED LEADER-FOLLOWER DETECTION ===\n")

manufacturers = fetch_all_manufacturers()

for manufacturer in manufacturers:
    print(f"\n=== Manufacturer: {manufacturer} ===")

    shop_list = fetch_shops_for_manufacturer(manufacturer)
    if not shop_list:
        print(f"{manufacturer} için shop bulunamadı. Atlanıyor.")
        continue

    change_dates_dict = {}
    shop_profits = {}

    for shop in shop_list:
        shop_df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
        manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)

        if shop_df.empty or manufacturer_df.empty:
            print(f"{shop} için yeterli veri yok. Atlanıyor.")
            continue

        # Profit serisi
        profit_series = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)

        # Shop profits to be used later for simultaneous detection
        shop_profits[shop] = profit_series

        # Değişim günlerini bul
        change_dates = []
        profit_diff = profit_series.diff().fillna(0)

        for date, diff in profit_diff.items():
            if abs(diff) >= 1.99:  # Threshold olarak 1.99 kullanıyoruz
                change_dates.append(date)

        if change_dates:
            change_dates_dict[shop] = change_dates

    if not change_dates_dict:
        print(f"{manufacturer} için değişim tespit edilemedi.")
    else:
        print("\nDetected Change Dates:")
        for shop, dates in change_dates_dict.items():
            print(f"{shop}: {[d.strftime('%Y-%m-%d') for d in dates]}")

        # Leader-follower ilişkileri
        relations = detect_real_leader_follower(change_dates_dict, max_day_difference=7)

        if not relations:
            print("\nNo Leader-Follower relations found.")
        else:
            print("\nLeader-Follower Relations:")
            for leader, follower, leader_date, follower_date in relations:
                print(f"{follower} follows {leader} | Leader Change: {leader_date.date()}, Follower Change: {follower_date.date()}")

    ## --- BURADAN SONRA KALAN 2 FONKSİYONUN TESTLERİ BAŞLIYOR ---

    print("\n[Extra Feature Test] Cosine Similarity and Feature Matrix")

    if len(shop_profits) >= 2:
        # create_shop_features kullanımı
        X, y = create_shop_features(shop_list, manufacturer, start_date, end_date, max_delay_days=7)

        if X is not None and y is not None:
            print("Feature Matrix (X):")
            print(X)
            print("Labels (y):")
            print(y)
        else:
            print("Feature matrix oluşturulamadı.")

        # detect_simultaneous_shops kullanımı
        simultaneous_pairs, isolated_shops = detect_simultaneous_shops(shop_profits, similarity_threshold=0.98)

        print("\nSimultaneous Pairs:")
        for shop1, shop2, date, profit in simultaneous_pairs:
            print(f"{shop1} & {shop2} simultaneous at {date.date()} with profit: {profit}")

        print("\nIsolated Shops:")
        for shop, date, profit in isolated_shops:
            print(f"{shop} isolated at {date.date()} with profit: {profit}")

    else:
        print("Shop verisi yeterli değil. Feature ve Simultaneous Testler atlandı.")

print("\n=== COMPLETED ALL TESTS ===")

