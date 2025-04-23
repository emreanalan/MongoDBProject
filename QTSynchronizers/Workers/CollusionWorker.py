from PySide6.QtCore import QObject, Signal, Slot
import pandas as pd
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'Build')))
from DataRetrieval import fetch_all_manufacturers, fetch_shops_for_manufacturer, fetch_price_data_from_shop, fetch_manufacturer_data
from ShopFeatureEngineering import detect_real_leader_follower, calculate_profit_relative_to_manufacturer

class CollusionWorker(QObject):
    newOutput = Signal(str)
    finished = Signal()

    def __init__(self, start_date, end_date, threshold=1.99):
        super().__init__()
        self.start_date = start_date
        self.end_date = end_date
        self.threshold = threshold

    @Slot()
    def run(self):
        self.newOutput.emit("=== FULL AUTOMATED COLLUSION DETECTION REPORT ===")

        manufacturers = fetch_all_manufacturers()

        for manufacturer in manufacturers:
            self.newOutput.emit(f"\n=== Manufacturer: {manufacturer} ===")
            shop_list = fetch_shops_for_manufacturer(manufacturer)
            if not shop_list:
                self.newOutput.emit(f"{manufacturer} için shop bulunamadı.\n")
                continue

            self.newOutput.emit(f"\nShoplar: {', '.join(shop_list)}\n")

            change_dates_dict = {}
            all_profit_series = {}

            manufacturer_df = fetch_manufacturer_data(manufacturer, self.start_date, self.end_date)
            if manufacturer_df.empty:
                continue

            # === Shop verilerini paralel olarak çek ===
            shop_data_cache = {}
            with ThreadPoolExecutor() as executor:
                future_to_shop = {
                    executor.submit(fetch_price_data_from_shop, shop, manufacturer, self.start_date, self.end_date): shop
                    for shop in shop_list
                }
                for future in as_completed(future_to_shop):
                    shop = future_to_shop[future]
                    try:
                        shop_data_cache[shop] = future.result()
                    except Exception as e:
                        self.newOutput.emit(f"{shop} verisi çekilirken hata: {e}")
                        shop_data_cache[shop] = pd.DataFrame()

            for shop, shop_df in shop_data_cache.items():
                if shop_df.empty:
                    continue

                profit_series = calculate_profit_relative_to_manufacturer(shop_df, manufacturer_df)
                all_profit_series[shop] = profit_series

                profit_diff = profit_series.diff().fillna(0)
                change_dates = [date for date, diff in profit_diff.items() if abs(diff) >= self.threshold]

                if change_dates:
                    change_dates_dict[shop] = change_dates

            if not change_dates_dict:
                self.newOutput.emit("Değişim tespit edilemedi, Leader-Follower analizi yapılamadı.\n")
                self.newOutput.emit("=== Isolated Shops ===")
                for shop in shop_list:
                    profit_series = all_profit_series.get(shop, None)
                    if profit_series is not None and not profit_series.empty:
                        first_date = profit_series.index[0]
                        first_profit = profit_series.iloc[0]
                        self.newOutput.emit(f"{shop} isolated (First profit: {first_profit:.2f}%, Date: {first_date.date()})")
                    else:
                        self.newOutput.emit(f"{shop} isolated (No profit data available)")
            else:
                relations = detect_real_leader_follower(change_dates_dict, max_day_difference=7)

                if relations:
                    self.newOutput.emit("\n=== Leader-Follower İlişkileri ===")
                    for leader, follower, leader_date, follower_date in relations:
                        delay_days = (follower_date - leader_date).days
                        sign = "+" if delay_days >= 0 else "-"

                        leader_series = all_profit_series.get(leader, pd.Series(dtype=float))
                        follower_series = all_profit_series.get(follower, pd.Series(dtype=float))

                        leader_profit_before = leader_series[leader_series.index < leader_date].iloc[-1] if (leader_series.index < leader_date).any() else "N/A"
                        leader_profit_after = leader_series.get(leader_date, "N/A")

                        follower_profit_before = follower_series[follower_series.index < follower_date].iloc[-1] if (follower_series.index < follower_date).any() else "N/A"
                        follower_profit_after = follower_series.get(follower_date, "N/A")

                        def format_profit(p):
                            return f"{p:.2f}%" if isinstance(p, (int, float)) else "N/A"

                        leader_change = f"{format_profit(leader_profit_before)} → {format_profit(leader_profit_after)}"
                        follower_change = f"{format_profit(follower_profit_before)} → {format_profit(follower_profit_after)}"

                        self.newOutput.emit(
                            f"{follower} follows {leader} "
                            f"(Leader Date: {leader_date.date()}, Follower Date: {follower_date.date()}, "
                            f"Delay: {sign}{abs(delay_days)} Days, "
                            f"Leader Profit: {leader_change}, Follower Profit: {follower_change})"
                        )

                    leader_summary = {}
                    for leader, follower, _, _ in relations:
                        if leader not in leader_summary:
                            leader_summary[leader] = []
                        leader_summary[leader].append(follower)

                    self.newOutput.emit("\n=== Genel Lider-Takipçiler Özeti ===")
                    for leader, followers in leader_summary.items():
                        unique_followers = sorted(set(followers))
                        self.newOutput.emit(f"Leader -> {leader} | Followers -> {', '.join(unique_followers)}")
                else:
                    self.newOutput.emit("Leader-Follower ilişkisi bulunamadı.\n")

                related_shops = set()
                for leader, follower, _, _ in relations:
                    related_shops.add(leader)
                    related_shops.add(follower)

                isolated_shops = [shop for shop in shop_list if shop not in related_shops]

                if isolated_shops:
                    self.newOutput.emit("\n=== Isolated Shops ===")
                    for shop in isolated_shops:
                        profit_series = all_profit_series.get(shop, None)
                        if profit_series is not None and not profit_series.empty:
                            first_date = profit_series.index[0]
                            first_profit = profit_series.iloc[0]
                            self.newOutput.emit(f"{shop} isolated (First profit: {first_profit:.2f}%, Date: {first_date.date()})")
                        else:
                            self.newOutput.emit(f"{shop} isolated (No profit data available)")

            self.newOutput.emit("\n" + "="*70)

        self.newOutput.emit("\n=== COMPLETED FULL COLLUSION REPORT ===\n")
        self.finished.emit()