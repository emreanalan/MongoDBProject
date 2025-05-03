# CollusionDetector.py

from DataRetrieval import (
    fetch_all_manufacturers,
    fetch_shops_for_manufacturer,
    fetch_price_data_from_shop,
    fetch_manufacturer_data,
)
from generate_similarity_matrix import (
    detect_real_leader_follower,
    calculate_profit_relative_to_manufacturer,
)
import pandas as pd

start_date = "2025-01-01"
end_date = "2025-04-20"
threshold = 1.99  # Change detection threshold

print("\n=== FULL AUTOMATED COLLUSION DETECTION REPORT ===\n")

manufacturers = fetch_all_manufacturers()

for manufacturer in manufacturers:
    print(f"\n=== Manufacturer: {manufacturer} ===")

    shop_list = fetch_shops_for_manufacturer(manufacturer)
    if not shop_list:
        print(f"{manufacturer} için shop bulunamadı.\n")
        continue

    print(f"\nShoplar: {shop_list}\n")

    change_dates_dict = {}
    all_profit_series = {}

    for shop in shop_list:
        shop_df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
        manufacturer_df = fetch_manufacturer_data(manufacturer, start_date, end_date)

        if shop_df.empty or manufacturer_df.empty:
            continue

        profit_series = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
        all_profit_series[shop] = profit_series

        profit_diff = profit_series.diff().fillna(0)
        change_dates = [date for date, diff in profit_diff.items() if abs(diff) >= threshold]

        if change_dates:
            change_dates_dict[shop] = change_dates

    if not change_dates_dict:
        print("Değişim tespit edilemedi, Leader-Follower analizi yapılamadı.\n")

        print("=== Isolated Shops ===")
        for shop in shop_list:
            profit_series = all_profit_series.get(shop, None)
            if profit_series is not None and not profit_series.empty:
                first_date = profit_series.index[0]
                first_profit = profit_series.iloc[0]
                print(f"{shop} isolated (First profit: {first_profit:.2f}%, Date: {first_date.date()})")
            else:
                print(f"{shop} isolated (No profit data available)")
    else:
        relations = detect_real_leader_follower(change_dates_dict, max_day_difference=7)

        if relations:
            print("\n=== Leader-Follower İlişkileri ===")
            for leader, follower, leader_date, follower_date in relations:
                delay_days = (follower_date - leader_date).days
                sign = "+" if delay_days >= 0 else "-"

                # Önce profit seriesi al
                leader_series = all_profit_series.get(leader, pd.Series(dtype=float))
                follower_series = all_profit_series.get(follower, pd.Series(dtype=float))

                # Leader değişimi
                leader_profit_before = leader_series[leader_series.index < leader_date].iloc[-1] if (
                            leader_series.index < leader_date).any() else "N/A"
                leader_profit_after = leader_series.get(leader_date, "N/A")

                # Follower değişimi
                follower_profit_before = follower_series[follower_series.index < follower_date].iloc[-1] if (
                            follower_series.index < follower_date).any() else "N/A"
                follower_profit_after = follower_series.get(follower_date, "N/A")

                # Güzel formatla
                def format_profit(p):
                    return f"{p:.2f}%" if isinstance(p, (int, float)) else "N/A"

                leader_change = f"{format_profit(leader_profit_before)} → {format_profit(leader_profit_after)}"
                follower_change = f"{format_profit(follower_profit_before)} → {format_profit(follower_profit_after)}"

                print(
                    f"{follower} follows {leader} "
                    f"(Leader Date: {leader_date.date()}, Follower Date: {follower_date.date()}, "
                    f"Delay: {sign}{abs(delay_days)} Days, "
                    f"Leader Profit: {leader_change}, Follower Profit: {follower_change})"
                )

            # --- Genel Özet ---
            leader_summary = {}
            for leader, follower, _, _ in relations:
                if leader not in leader_summary:
                    leader_summary[leader] = []
                leader_summary[leader].append(follower)

            print("\n=== Genel Lider-Takipçiler Özeti ===")
            for leader, followers in leader_summary.items():
                unique_followers = sorted(set(followers))
                print(f"Leader -> {leader} | Followers -> {', '.join(unique_followers)}")
        else:
            print("Leader-Follower ilişkisi bulunamadı.\n")

        # --- İlişkili Shoplar ---
        related_shops = set()
        for leader, follower, _, _ in relations:
            related_shops.add(leader)
            related_shops.add(follower)

        isolated_shops = [shop for shop in shop_list if shop not in related_shops]

        if isolated_shops:
            print("\n=== Isolated Shops ===")
            for shop in isolated_shops:
                profit_series = all_profit_series.get(shop, None)
                if profit_series is not None and not profit_series.empty:
                    first_date = profit_series.index[0]
                    first_profit = profit_series.iloc[0]
                    print(f"{shop} isolated (First profit: {first_profit:.2f}%, Date: {first_date.date()})")
                else:
                    print(f"{shop} isolated (No profit data available)")

    print("\n" + "="*70)

print("\n=== COMPLETED FULL COLLUSION REPORT ===\n")
