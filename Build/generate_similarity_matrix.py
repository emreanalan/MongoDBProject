import os
import json
from glob import glob
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm
import multiprocessing
from sklearn.metrics.pairwise import cosine_similarity

SHOP_DATA_DIR = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops2"
OUTPUT_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_similarity_matrixTest1.csv"


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
    delay_count = 0
    overlap_count = 0
    total_common_products = 0
    profit_diffs = []

    for product in data_a:
        if product in data_b:
            days_a = set(data_a[product].keys())
            days_b = set(data_b[product].keys())
            total_common_products += 1
            for d1 in days_a:
                dt1 = datetime.strptime(d1, "%Y-%m-%d")
                for delay in range(0, 8):
                    dt2 = dt1 + timedelta(days=delay)
                    d2_str = dt2.strftime("%Y-%m-%d")
                    if d2_str in days_b:
                        if delay == 0:
                            overlap_count += 1
                        else:
                            delay_count += 1
                        pa = data_a[product][d1]
                        pb = data_b[product][d2_str]
                        profit_diffs.append(abs(pa - pb))
                        break

    if total_common_products == 0:
        return (id1, id2, 0, 0, 0)

    delay_score = delay_count / total_common_products
    overlap_score = overlap_count / total_common_products
    profit_similarity = 1 - (np.mean(profit_diffs) / 100) if profit_diffs else 0
    return (id1, id2, delay_score, overlap_score, profit_similarity)


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
            id1, id2, d, o, p = result
            results.append({
                "shop_id_1": id1,
                "shop_id_2": id2,
                "delay_score": d,
                "overlap_score": o,
                "profit_similarity": p
            })

    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Similarity matrisi kaydedildi: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()