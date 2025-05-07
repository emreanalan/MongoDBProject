import os
import json
from glob import glob
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool

SHOP_DATA_DIR = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops2"
OUTPUT_FEATURES_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features2.csv"
OUTPUT_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_similarity_matrixTest1.csv"


COLLUSION_GROUPS = {
    1: [56, 11, 74, 20, 76, 1, 18, 22, 36, 78],
    2: [5, 30, 34, 82, 2, 99, 40, 45, 67, 15],
    3: [13, 77, 80, 7, 59, 91, 70, 31, 68, 73],
    4: [33, 17, 43, 24, 88, 47, 90, 62, 61, 28],
    5: [69, 50, 21, 84, 58, 64, 75, 97, 16, 25],
    6: [89, 95, 42, 93, 41, 66, 55, 37, 65, 46],
}



COLLUSION_SHOP_IDS = {shop_id for group in COLLUSION_GROUPS.values() for shop_id in group}
SHOP_ID_TO_GROUP = {shop_id: group_id for group_id, shop_list in COLLUSION_GROUPS.items() for shop_id in shop_list}

def parse_profit(profit):
    try:
        return float(str(profit).replace("%", ""))
    except:
        return 0.0

def extract_product_price_history(shop_path):
    with open(shop_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    product_history = defaultdict(list)
    for day_record in records:
        date = day_record["Date"]
        for key in day_record:
            if key.endswith("Products"):
                prod_data = day_record[key]
                for sub_key in prod_data:
                    if sub_key.endswith("Shop Profit %"):
                        product_name = sub_key.replace(" Shop Profit %", "")
                        profit = parse_profit(prod_data[sub_key])
                        product_history[product_name].append((date, profit))
    return product_history

def compute_similarity_worker(args):
    id1, id2, data_a, data_b = args
    total_common_products = 0
    total_profit_diffs = []
    matched_zam_days = 0
    delay_within_4_days = 0

    for product in data_a:
        if product in data_b:
            # 'data_a[product]' ve 'data_b[product]' veri yapısını kontrol et
            if isinstance(data_a[product], dict) and isinstance(data_b[product], dict):
                days_a = sorted(data_a[product].keys())
                days_b = sorted(data_b[product].keys())
                total_common_products += 1

                for d1 in days_a:
                    dt1 = datetime.strptime(d1, "%Y-%m-%d")
                    for delay in range(0, 5):  # Delay 0–4 gün arası
                        dt2 = dt1 + timedelta(days=delay)
                        d2_str = dt2.strftime("%Y-%m-%d")
                        if d2_str in data_b[product]:
                            profit_a = data_a[product][d1]
                            profit_b = data_b[product][d2_str]
                            diff = abs(profit_a - profit_b)
                            total_profit_diffs.append(diff)

                            if delay == 0:
                                matched_zam_days += 1
                            delay_within_4_days += 1
                            break
            else:
                # Eğer 'data_a[product]' veya 'data_b[product]' dict değilse, hata vermek yerine bir şey yapma.
                continue

    if total_common_products == 0:
        return (id1, id2, 0, 0, 0)

    price_similarity = 1 - (np.mean(total_profit_diffs) / 100) if total_profit_diffs else 0
    zam_day_overlap = matched_zam_days / total_common_products
    delay_alignment = delay_within_4_days / total_common_products

    return (id1, id2, price_similarity, zam_day_overlap, delay_alignment)

def compute_product_price_diff(product_history):
    price_diff_list = []
    for product, records in product_history.items():
        records.sort()
        if len(records) > 1:
            prices = [profit for _, profit in records]
            price_diff = np.std(prices)
            price_diff_list.append(price_diff)
    return np.mean(price_diff_list) if price_diff_list else 0

def compute_product_price_variance(product_history):
    price_variance_list = []
    for product, records in product_history.items():
        if len(records) > 1:
            prices = [profit for _, profit in records]
            price_variance = np.var(prices)
            price_variance_list.append(price_variance)
    return np.mean(price_variance_list) if price_variance_list else 0

def compute_price_change_frequency(shop_path, product_history):
    price_changes = 0
    for product, records in product_history.items():
        if len(records) > 1:
            for i in range(1, len(records)):
                if records[i][1] != records[i-1][1]:
                    price_changes += 1
    return price_changes

def compute_profit_percentage_variability(shop_path, product_history):
    profit_variations = []
    for product, records in product_history.items():
        if len(records) > 1:
            profits = [profit for _, profit in records]
            profit_variations.append(np.std(profits))
    return np.mean(profit_variations) if profit_variations else 0

def compute_product_price_consistency(shop_id, product_history, all_shop_profits):
    price_consistency = []
    for product, records in product_history.items():
        prices = [profit for _, profit in records]
        avg_price = np.mean(prices)
        group_prices = []
        for other_id, other_product_history in all_shop_profits.items():
            if other_id == shop_id:
                continue
            if product in other_product_history:
                group_prices.append(np.mean([p for _, p in other_product_history[product]]))
        price_consistency.append(np.std(group_prices) / avg_price if group_prices else 0)
    return np.mean(price_consistency) if price_consistency else 0


def extract_features(args):
    shop_path, all_shop_profits = args
    shop_id = int(os.path.basename(shop_path).split()[1].split(".")[0])
    product_history = extract_product_price_history(shop_path)

    price_change_count = len(product_history)
    product_price_diff = compute_product_price_diff(product_history)
    product_price_variance = compute_product_price_variance(product_history)
    price_change_frequency = compute_price_change_frequency(shop_path, product_history)
    profit_percentage_variability = compute_profit_percentage_variability(shop_path, product_history)
    product_price_consistency = compute_product_price_consistency(shop_id, product_history, all_shop_profits)

    manufacturer_set = set()
    profit_values = []
    with open(shop_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        for day_record in records:
            for key in day_record:
                if key.endswith("Products"):
                    manufacturer_set.add(key.split()[0])
                    for sub_key in day_record[key]:
                        if sub_key.endswith("Shop Profit %"):
                            profit = parse_profit(day_record[key][sub_key])
                            profit_values.append(profit)

    return {
        "shop_id": shop_id,
        "price_change_count": price_change_count,
        "product_price_diff": product_price_diff,
        "product_price_variance": product_price_variance,
        "price_change_frequency": price_change_frequency,
        "profit_percentage_variability": profit_percentage_variability,
        "product_price_consistency": product_price_consistency,
        "manufacturer_count": len(manufacturer_set),
        "avg_profit_pct": np.mean(profit_values) if profit_values else 0,
        "profit_pct_std": np.std(profit_values) if profit_values else 0,
        "is_collusion": int(shop_id in COLLUSION_SHOP_IDS),
        "collusion_group": SHOP_ID_TO_GROUP.get(shop_id, -1)
    }

def main():
    shop_files = glob(os.path.join(SHOP_DATA_DIR, "Shop *.json"))
    shop_ids = [int(os.path.basename(p).split()[1].split(".")[0]) for p in shop_files]
    shop_data = {}

    print("📦 Shop verileri yükleniyor...")
    for shop_file in tqdm(shop_files, desc="Shop yükleme"):
        shop_id = int(os.path.basename(shop_file).split()[1].split(".")[0])
        shop_data[shop_id] = extract_product_price_history(shop_file)

    print("⚙️ Paralel karşılaştırma başlıyor...")
    args_list = []
    for i in range(len(shop_ids)):
        for j in range(i + 1, len(shop_ids)):
            id1 = shop_ids[i]
            id2 = shop_ids[j]
            args_list.append((id1, id2, shop_data[id1], shop_data[id2]))

    results = []
    with Pool() as pool:
        for result in tqdm(pool.imap_unordered(compute_similarity_worker, args_list), total=len(args_list)):
            id1, id2, price_sim, zam_overlap, delay_score = result
            results.append({
                "shop_id_1": id1,
                "shop_id_2": id2,
                "price_similarity": price_sim,
                "zam_day_overlap": zam_overlap,
                "delay_alignment": delay_score
            })

    similarity_df = pd.DataFrame(results)
    similarity_df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Similarity matrisi kaydedildi: {OUTPUT_CSV}")

    all_shop_profits = {
        int(os.path.basename(f).split()[1].split(".")[0]): extract_product_price_history(f)
        for f in tqdm(shop_files, desc="Ön bellekleme")
    }
    args = [(f, all_shop_profits) for f in shop_files]
    with Pool() as pool:
        features = list(tqdm(pool.imap_unordered(extract_features, args), total=len(shop_files), desc="Özellik çıkarımı"))
    df = pd.DataFrame(features)
    df.to_csv(OUTPUT_FEATURES_CSV, index=False)
    print(f"✅ Özellik dosyası kaydedildi: {OUTPUT_FEATURES_CSV}")

if __name__ == "__main__":
    main()
