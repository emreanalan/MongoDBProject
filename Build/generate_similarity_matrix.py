import os
import json
from glob import glob
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm
import multiprocessing

SHOP_DATA_DIR = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops"
OUTPUT_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_similarity_matrix1.csv"


def extract_product_price_history(shop_path):
    with open(shop_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    product_history = defaultdict(dict)
    for day_record in records:
        date = day_record["Date"]
        for key in day_record:
            if key.endswith("Products"):
                prod_data = day_record[key]
                for sub_key in prod_data:
                    if sub_key.endswith("Shop Profit %"):
                        product_name = sub_key.replace(" Shop Profit %", "")
                        profit = prod_data[sub_key]
                        product_history[product_name][date] = profit
    return product_history


def compute_similarity_worker(args):
    id1, id2, data_a, data_b = args
    total_common_products = 0
    total_profit_diffs = []
    matched_zam_days = 0
    delay_within_4_days = 0

    for product in data_a:
        if product in data_b:
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

    if total_common_products == 0:
        return (id1, id2, 0, 0, 0)

    price_similarity = 1 - (np.mean(total_profit_diffs) / 100) if total_profit_diffs else 0
    zam_day_overlap = matched_zam_days / total_common_products
    delay_alignment = delay_within_4_days / total_common_products

    return (id1, id2, price_similarity, zam_day_overlap, delay_alignment)


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
    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        for result in tqdm(pool.imap_unordered(compute_similarity_worker, args_list), total=len(args_list)):
            id1, id2, price_sim, zam_overlap, delay_score = result
            results.append({
                "shop_id_1": id1,
                "shop_id_2": id2,
                "price_similarity": price_sim,
                "zam_day_overlap": zam_overlap,
                "delay_alignment": delay_score
            })

    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Similarity matrisi kaydedildi: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
