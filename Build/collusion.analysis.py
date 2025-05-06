import os
import json
from glob import glob
from collections import defaultdict
import numpy as np
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool

SHOP_DATA_DIR = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops"
OUTPUT_FEATURES_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv"

COLLUSION_GROUPS = {
    1: [40, 235, 339, 245, 197, 323, 302, 182, 166, 238],
    2: [319, 16, 67, 172, 332, 21, 255, 12, 265, 75],
    3: [279, 119, 384, 220, 26, 375, 327, 33, 224, 196],
    4: [108, 377, 136, 276, 263, 55, 129, 396, 109, 78],
    5: [118, 234, 395, 30, 7, 159, 41, 160, 207, 130],
    6: [343, 314, 259, 151, 25, 320, 380, 258, 346, 393],
    7: [103, 290, 366, 199, 344, 231, 365, 241, 195, 87],
    8: [248, 308, 225, 183, 269, 387, 74, 371, 353, 192],
    9: [372, 388, 165, 60, 244, 394, 331, 79, 179, 187],
    10: [233, 115, 174, 53, 189, 280, 253, 6, 246, 277],
    11: [66, 201, 383, 101, 200, 205, 120, 285, 44, 378],
    12: [32, 4, 9, 185, 163, 333, 106, 83, 296, 321],
    13: [2, 262, 81, 325, 272, 59, 214, 256, 232, 305],
    14: [247, 138, 23, 306, 202, 313, 99, 328, 283, 278],
    15: [293, 178, 126, 147, 47, 359, 5, 361, 177, 31],
    16: [289, 307, 209, 301, 110, 148, 132, 173, 80, 8],
    17: [391, 287, 284, 3, 369, 88, 385, 273, 291, 354],
    18: [149, 299, 111, 254, 322, 355, 69, 57, 275, 104],
    19: [204, 348, 77, 266, 181, 121, 249, 114, 243, 128],
    20: [29, 351, 146, 36, 125, 329, 218, 105, 316, 72],
    21: [336, 342, 10, 145, 123, 186, 37, 137, 117, 229],
    22: [337, 222, 267, 52, 386, 228, 176, 91, 134, 141],
    23: [156, 382, 180, 50, 297, 155, 360, 191, 18, 398],
    24: [286, 381, 42, 70, 1, 193, 363, 237, 17, 221],
    25: [211, 158, 347, 373, 309, 157, 324, 379, 376, 340],
    26: [274, 28, 150, 251, 124, 374, 226, 294, 90, 356],
    27: [122, 213, 89, 250, 358, 239, 219, 64, 349, 127],
    28: [46, 171, 14, 230, 133, 217, 390, 188, 295, 303],
    29: [317, 335, 236, 19, 24, 107, 330, 35, 45, 210],
    30: [364, 288, 184, 131, 56, 270, 71, 39, 300, 84],
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

def compute_price_similarity(shop_id, product_history, all_shop_profits):
    similarity_scores = []
    for product, records in product_history.items():
        prices = [profit for _, profit in records]
        avg_price = np.mean(prices)
        group_prices = []
        for other_id, other_product_history in all_shop_profits.items():
            if other_id == shop_id:
                continue
            if product in other_product_history:
                group_prices.append(np.mean([p for _, p in other_product_history[product]]))
        if group_prices:
            price_similarity = np.std(group_prices) / avg_price
            similarity_scores.append(price_similarity)
    return np.mean(similarity_scores) if similarity_scores else 0


def compute_price_change_correlation(shop_id, product_history, all_shop_profits):
    correlation_scores = []
    for product, records in product_history.items():
        if len(records) > 1:
            price_changes = [profit for _, profit in records]
            correlations = []
            for other_id, other_product_history in all_shop_profits.items():
                if other_id == shop_id:
                    continue
                if product in other_product_history:
                    other_price_changes = [profit for _, profit in other_product_history[product]]

                    # Eşit uzunlukta olmaları gerekiyor, kısa olanı uzun olana göre keselim
                    min_length = min(len(price_changes), len(other_price_changes))
                    price_changes = price_changes[:min_length]
                    other_price_changes = other_price_changes[:min_length]

                    # Pearson korelasyonunu hesapla
                    correlation = np.corrcoef(price_changes, other_price_changes)[0, 1]
                    correlations.append(correlation)
            if correlations:
                correlation_scores.append(np.mean(correlations))
    return np.mean(correlation_scores) if correlation_scores else 0


def compute_zam_day_overlap_with_delay(shop_id, product_history, all_shop_profits):
    zam_days = set()
    for day_record in product_history.values():
        zam_days.add(day_record[0][0])  # Assume price change days are the first record's date
    overlap_count = 0
    for other_id, other_product_history in all_shop_profits.items():
        if other_id == shop_id:
            continue
        other_zam_days = set()
        for day_record in other_product_history.values():
            other_zam_days.add(day_record[0][0])
        overlap_count += len(zam_days.intersection(other_zam_days))
    return overlap_count / len(zam_days) if zam_days else 0

def compute_manufacturer_overlap(shop_id, product_history, all_shop_profits):
    manufacturer_set = set()
    for product in product_history:
        manufacturer_set.add(product.split()[0])  # Assuming manufacturer is part of the product name
    overlap_scores = []
    for other_id, other_product_history in all_shop_profits.items():
        if other_id == shop_id:
            continue
        other_manufacturer_set = set()
        for product in other_product_history:
            other_manufacturer_set.add(product.split()[0])
        overlap = len(manufacturer_set.intersection(other_manufacturer_set)) / len(manufacturer_set)
        overlap_scores.append(overlap)
    return np.mean(overlap_scores) if overlap_scores else 0

def extract_features(args):
    shop_path, all_shop_profits = args
    shop_id = int(os.path.basename(shop_path).split()[1].split(".")[0])
    product_history = extract_product_price_history(shop_path)

    price_similarity = compute_price_similarity(shop_id, product_history, all_shop_profits)
    price_change_correlation = compute_price_change_correlation(shop_id, product_history, all_shop_profits)
    zam_day_overlap_with_delay = compute_zam_day_overlap_with_delay(shop_id, product_history, all_shop_profits)
    manufacturer_overlap = compute_manufacturer_overlap(shop_id, product_history, all_shop_profits)

    return {
        "shop_id": shop_id,
        "price_similarity_score": price_similarity,
        "price_change_correlation": price_change_correlation,
        "zam_day_overlap_with_delay": zam_day_overlap_with_delay,
        "manufacturer_overlap": manufacturer_overlap,
        "is_collusion": int(shop_id in COLLUSION_SHOP_IDS),
        "collusion_group": SHOP_ID_TO_GROUP.get(shop_id, -1)
    }

def main():
    shop_files = glob(os.path.join(SHOP_DATA_DIR, "Shop *.json"))
    all_shop_profits = {
        int(os.path.basename(f).split()[1].split(".")[0]): extract_product_price_history(f)
        for f in tqdm(shop_files, desc="Ön bellekleme")
    }
    args = [(f, all_shop_profits) for f in shop_files]
    with Pool() as pool:
        features = list(tqdm(pool.imap_unordered(extract_features, args), total=len(shop_files), desc="Özellik çıkarımı"))
    df = pd.DataFrame(features)
    print("\n📊 İlk 20 özellik satırı:")
    print(df.head(20).to_string(index=False))  # Daha düzgün görünüm için index=False

    df.to_csv(OUTPUT_FEATURES_CSV, index=False)
    print(f"✅ Özellik dosyası kaydedildi: {OUTPUT_FEATURES_CSV}")

if __name__ == "__main__":
    main()
