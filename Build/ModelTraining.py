import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from DataRetrieval import fetch_all_manufacturers, fetch_shops_for_manufacturer, fetch_price_data_from_shop, fetch_manufacturer_data, find_profit_change_dates
from ShopFeatureEngineering import create_shop_features, calculate_profit_relative_to_manufacturer, detect_real_leader_follower

start_date = "2023-01-18"
end_date = "2025-04-18"

manufacturers = fetch_all_manufacturers()

for manufacturer in manufacturers:
    print(f"\n=== Manufacturer: {manufacturer} ===")

    shop_list = fetch_shops_for_manufacturer(manufacturer)
    print("Shoplar:", shop_list)

    if len(shop_list) < 2:
        print("Yeterli shop verisi bulunamadı.")
        print(f"{manufacturer} için yeterli feature yok, atlanıyor.")
        continue

    manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)
    if manufacturer_df.empty:
        print(f"{manufacturer} için üretici verisi bulunamadı.")
        continue

    X, y = create_shop_features(shop_list, manufacturer, start_date, end_date)

    if X is None or y is None or len(np.unique(y)) < 2 or min(np.bincount(y)) < 2:
        print(f"{manufacturer} için eğitim verisinde yeterli veri yok. Model eğitilemiyor, atlanıyor.")
        continue

    print(f"Feature boyutu: {X.shape}, Label boyutu: {y.shape}")
    print("Label dağılımı:", np.bincount(y))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    model = LogisticRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("\n=== Model Evaluation ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}\n")
    print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # --- Leader-Follower Tespiti --- (Real Profit Change Dates üzerinden)
    change_dates_dict = {}
    shop_profits = {}

    for shop in shop_list:
        shop_df = fetch_price_data_from_shop(shop, start_date, end_date)
        if not shop_df.empty:
            manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)
            profits = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
            shop_profits[shop] = profits

            changes = find_profit_change_dates(shop_df, manufacturer_df)
            change_dates_dict[shop] = [cd[0] for cd in changes]

    if change_dates_dict:
        relationships = detect_real_leader_follower(change_dates_dict, max_day_difference=10)

        if relationships:
            print("\n=== Leader-Follower İlişkileri ===")
            leader_counts = {}

            for leader, follower, leader_date, follower_date in relationships:
                leader_profit_start = shop_profits.get(leader, pd.Series()).get(leader_date, np.nan)
                follower_profit_end = shop_profits.get(follower, pd.Series()).get(follower_date, np.nan)

                print(f"{follower} follows {leader} (Leader Date: {leader_date.strftime('%Y-%m-%d')}, "
                      f"Follower Date: {follower_date.strftime('%Y-%m-%d')})")

                if leader not in leader_counts:
                    leader_counts[leader] = []

                leader_counts[leader].append({
                    "follower": follower,
                    "start_date": leader_date,
                    "end_date": follower_date,
                    "change_start": leader_profit_start,
                    "change_end": follower_profit_end
                })

            print("\n=== Genel Lider- Takipçiler Özeti ===")
            if leader_counts:
                for leader, follower_info_list in leader_counts.items():
                    outputs = []
                    seen_followers = set()
                    for info in follower_info_list:
                        if info['follower'] not in seen_followers:
                            seen_followers.add(info['follower'])
                            outputs.append(
                                f"{info['follower']} (Start: {info['start_date'].strftime('%Y-%m-%d')}, "
                                f"End: {info['end_date'].strftime('%Y-%m-%d')}, "
                                f"Change: {info['change_start']:.2f}% → {info['change_end']:.2f}%)"
                            )
                    print(f"Leader -> {leader} | Followers -> {', '.join(outputs)}")
            else:
                print("Belirgin bir lider bulunamadı.")
        else:
            print("\nLeader-Follower ilişkisi bulunamadı.")
