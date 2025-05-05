import os
import json
from glob import glob
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool

SHOP_DATA_DIR = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops"
OUTPUT_FEATURES_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv"

COLLUSION_GROUPS = {
    1: [206, 24, 33], 2: [164, 57, 174], 3: [246, 317, 349], 4: [169, 138, 343],
    5: [218, 60, 153, 399], 6: [78, 160, 320], 7: [347, 139, 199], 8: [225, 83, 167],
    9: [273, 373, 187, 31], 10: [110, 369, 217, 259, 323], 11: [275, 350, 230, 130, 38],
    12: [330, 111, 345, 190, 18], 13: [336, 147, 173, 387], 14: [265, 254, 232, 372, 148],
    15: [172, 315, 316, 34], 16: [84, 353, 103, 381, 329], 17: [354, 17, 376],
    18: [65, 135, 270, 331, 359], 19: [140, 289, 6, 3], 20: [374, 93, 357],
    21: [76, 157, 342], 22: [131, 386, 101], 23: [327, 221, 303],
    24: [249, 122, 26, 299], 25: [318, 278, 192, 352], 26: [116, 227, 128, 9, 371],
    27: [88, 311, 42, 19, 292], 28: [314, 392, 46, 114], 29: [189, 222, 145, 87],
    30: [29, 396, 358], 31: [13, 228, 161], 32: [240, 180, 129, 21],
    33: [94, 163, 271, 364, 12], 34: [16, 177, 150, 142], 35: [32, 324, 121],
    36: [165, 291, 389, 155], 37: [80, 143, 119, 201], 38: [113, 197, 186],
    39: [212, 209, 319], 40: [356, 178, 8, 184], 41: [379, 281, 55, 64, 30],
    42: [66, 51, 332], 43: [298, 58, 214, 306], 44: [132, 90, 40],
    45: [202, 220, 127, 264, 257], 46: [95, 43, 384, 368, 195],
    47: [391, 321, 313], 48: [378, 205, 22], 49: [312, 250, 223, 1],
    50: [28, 276, 52, 280, 100], 51: [162, 56, 54],
    52: [47, 75, 120, 211, 334], 53: [144, 27, 67, 253, 393],
    54: [118, 248, 194, 252], 55: [96, 279, 307], 56: [207, 367, 296, 301],
    57: [337, 305, 288, 198, 302], 58: [297, 261, 191, 251, 274],
    59: [71, 383, 310, 35], 60: [20, 152, 185], 61: [326, 154, 85, 134],
    62: [151, 204, 25, 82], 63: [215, 89, 73, 322, 355],
    64: [269, 98, 105, 304, 69], 65: [333, 4, 287, 92, 79], 66: [263, 2, 294],
    67: [233, 285, 235], 68: [335, 390, 68, 141, 266],
    69: [196, 338, 341, 203], 70: [377, 308, 286, 224],
    71: [14, 394, 125], 72: [200, 351, 243, 115, 11],
    73: [170, 37, 219, 216, 210], 74: [23, 39, 244, 234, 171],
    75: [268, 339, 63], 76: [74, 267, 365, 229]
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

def compute_delay_overlap_similarity(product_history):
    delay_list = []
    overlap_list = []
    all_profits = []
    for product, records in product_history.items():
        records.sort()
        for i in range(1, len(records)):
            prev_date = datetime.strptime(records[i-1][0], "%Y-%m-%d")
            curr_date = datetime.strptime(records[i][0], "%Y-%m-%d")
            delay = (curr_date - prev_date).days
            delay_list.append(int(0 <= delay <= 4))
            overlap_list.append(int(delay == 0))
            all_profits.append(abs(records[i][1] - records[i-1][1]))
    avg_delay_score = np.mean(delay_list) if delay_list else 0
    avg_zam_overlap = np.mean(overlap_list) if overlap_list else 0
    avg_price_similarity = 1 - (np.mean(all_profits) / 100) if all_profits else 0
    return avg_price_similarity, avg_zam_overlap, avg_delay_score

def compute_price_std_similarity(shop_id, shop_products, all_shop_profits, max_compare=20):
    diffs = []
    count = 0
    for other_id, other_products in all_shop_profits.items():
        if other_id == shop_id:
            continue
        for product in shop_products:
            if product in other_products:
                p1 = [v for _, v in shop_products[product]]
                p2 = [v for _, v in other_products[product]]
                if p1 and p2:
                    try:
                        diff = np.std(np.array(p1) - np.array(p2))
                        diffs.append(diff)
                        break
                    except:
                        continue
        count += 1
        if count >= max_compare:
            break
    return np.mean(diffs) if diffs else 0

def compute_top_k_neighbor_overlap(shop_id, shop_products, all_shop_profits, k=5):
    similarities = []
    for other_id, other_products in all_shop_profits.items():
        if other_id == shop_id:
            continue
        common_products = set(shop_products.keys()) & set(other_products.keys())
        total_overlap = 0
        total_count = 0
        for product in common_products:
            dates_a = set(d for d, _ in shop_products[product])
            dates_b = set(d for d, _ in other_products[product])
            total_overlap += len(dates_a & dates_b)
            total_count += len(dates_a | dates_b)
        similarity = total_overlap / total_count if total_count else 0
        similarities.append(similarity)
    similarities.sort(reverse=True)
    return np.mean(similarities[:k]) if similarities else 0

def compute_productwise_variance(shop_id, shop_products, all_shop_profits):
    variances = []
    for product in shop_products:
        prices = []
        for other_id, other_products in all_shop_profits.items():
            if product in other_products:
                prices.extend([v for _, v in other_products[product]])
        if prices:
            variances.append(np.var(prices))
    return np.mean(variances) if variances else 0

def extract_features(args):
    shop_path, all_shop_profits = args
    shop_id = int(os.path.basename(shop_path).split()[1].split(".")[0])
    product_history = extract_product_price_history(shop_path)

    price_change_count = 0
    profit_values = []
    manufacturer_set = set()
    all_dates = set()
    with open(shop_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        for day_record in records:
            all_dates.add(day_record["Date"])
            price_change_count += 1
            for key in day_record:
                if key.endswith("Products"):
                    manufacturer_set.add(key.split()[0])
                    for sub_key in day_record[key]:
                        if sub_key.endswith("Shop Profit %"):
                            profit = parse_profit(day_record[key][sub_key])
                            profit_values.append(profit)

    date_objs = sorted(datetime.strptime(d, "%Y-%m-%d") for d in all_dates)
    day_diffs = [(date_objs[i+1] - date_objs[i]).days for i in range(len(date_objs)-1)]
    avg_interval = np.mean(day_diffs) if day_diffs else 0

    avg_price_similarity, avg_zam_overlap, avg_delay_score = compute_delay_overlap_similarity(product_history)
    price_std_similarity = compute_price_std_similarity(shop_id, product_history, all_shop_profits)
    top_k_neighbor_overlap = compute_top_k_neighbor_overlap(shop_id, product_history, all_shop_profits)
    productwise_variance = compute_productwise_variance(shop_id, product_history, all_shop_profits)

    return {
        "shop_id": shop_id,
        "price_change_count": price_change_count,
        "avg_day_between_changes": avg_interval,
        "manufacturer_count": len(manufacturer_set),
        "avg_profit_pct": np.mean(profit_values) if profit_values else 0,
        "profit_pct_std": np.std(profit_values) if profit_values else 0,
        "product_count": len(product_history),
        "avg_price_similarity": avg_price_similarity,
        "avg_zam_overlap": avg_zam_overlap,
        "avg_delay_score": avg_delay_score,
        "price_std_similarity": price_std_similarity,
        "top_k_neighbor_overlap": top_k_neighbor_overlap,
        "productwise_variance_across_shops": productwise_variance,
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
    df.to_csv(OUTPUT_FEATURES_CSV, index=False)
    print(f"✅ Özellik dosyası kaydedildi: {OUTPUT_FEATURES_CSV}")

if __name__ == "__main__":
    main()
