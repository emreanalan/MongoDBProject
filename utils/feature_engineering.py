import os
import json
import numpy as np
from datetime import datetime, timedelta
from glob import glob
from collections import defaultdict
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import multiprocessing
import pandas as pd

SHOP_DATA_DIR = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops"
COLLUSION_GROUPS = {
    1: [47, 12, 88, 99, 98],
    2: [41, 63, 18, 44, 42],
    3: [34, 2, 85],
    4: [23, 40, 75],
    5: [50, 67, 84],
    6: [60, 19, 65, 49],
    7: [48, 15, 11, 26],
    8: [74, 96, 53, 33],
    9: [59, 70, 29, 90, 10],
    10: [35, 80, 30, 52],
    11: [54, 68, 76, 45],
    12: [62, 86, 21, 46, 55, 78]
}

COLLUSION_SHOPS = {shop_id: group for group, shops in COLLUSION_GROUPS.items() for shop_id in shops}

similarity_cache = {}

def parse_price(price_str):
    return float(price_str.replace("TL", "").replace(",", "").strip())

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
                        profit = prod_data[sub_key]
                        product_history[product_name].append((date, profit))
    return product_history

def compute_product_based_similarity(shop_id, shop_product_days, all_shops_product_days, all_shops_profit):
    if shop_id in similarity_cache:
        return similarity_cache[shop_id]

    delays = []
    overlaps = []
    profit_similarities = []
    for other_id, other_product_days in all_shops_product_days.items():
        if other_id == shop_id:
            continue
        delay_count = 0
        overlap_count = 0
        total_common_products = 0
        profit_diffs = []

        for product in shop_product_days:
            if product in other_product_days:
                days_a = set([d for d, _ in shop_product_days[product]])
                days_b = set([d for d, _ in all_shops_profit[other_id][product]])
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
                            pa = [p for dd, p in shop_product_days[product] if dd == d1]
                            pb = [p for dd, p in all_shops_profit[other_id][product] if dd == d2_str]
                            if pa and pb:
                                profit_diffs.append(abs(pa[0] - pb[0]))
                            break

        if total_common_products > 0:
            delays.append(delay_count / total_common_products)
            overlaps.append(overlap_count / total_common_products)
            if profit_diffs:
                profit_similarities.append(1 - (np.mean(profit_diffs) / 100))

    avg_delay_score = np.mean(delays) if delays else 0
    exact_overlap_ratio = np.mean(overlaps) if overlaps else 0
    avg_profit_similarity = np.mean(profit_similarities) if profit_similarities else 0
    similarity_cache[shop_id] = (avg_delay_score, exact_overlap_ratio, avg_profit_similarity)
    return similarity_cache[shop_id]

def extract_shop_features_parallel(args):
    shop_path, all_shops_product_days, all_shops_profit = args
    return extract_shop_features(shop_path, all_shops_product_days, all_shops_profit)

def extract_shop_features(shop_path, all_shops_product_days, all_shops_profit):
    shop_id = int(os.path.basename(shop_path).split()[1].split(".")[0])
    product_days = extract_product_price_history(shop_path)

    all_dates = set()
    profit_percentages = []
    manufacturer_set = set()

    with open(shop_path, "r", encoding="utf-8") as f:
        records = json.load(f)
        for day_record in records:
            all_dates.add(day_record["Date"])
            for key in day_record:
                if key.endswith("Products"):
                    manufacturer_set.add(key.split()[0])
                    prod_data = day_record[key]
                    for sub_key in prod_data:
                        if sub_key.endswith("Shop Profit %"):
                            profit_percentages.append(prod_data[sub_key])

    sorted_dates = sorted(all_dates)
    date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
    date_diffs = np.diff(sorted(date_objs))
    day_intervals = [d.days for d in date_diffs]

    delay_score, overlap_score, profit_similarity = compute_product_based_similarity(shop_id, product_days, all_shops_product_days, all_shops_profit)

    return {
        "shop_id": shop_id,
        "price_change_count": len(all_dates),
        "avg_day_between_changes": np.mean(day_intervals) if day_intervals else 0,
        "manufacturer_count": len(manufacturer_set),
        "avg_profit_pct": np.mean(profit_percentages) if profit_percentages else 0,
        "profit_pct_std": np.std(profit_percentages) if profit_percentages else 0,
        "product_count": len(product_days),
        "avg_delay_score": delay_score,
        "exact_overlap_ratio": overlap_score,
        "avg_profit_similarity": profit_similarity,
        "label_binary": 1 if shop_id in COLLUSION_SHOPS else 0,
        "label_group": COLLUSION_SHOPS.get(shop_id, -1)
    }

def visualize_similarity_graph(feature_list, threshold=0.99):
    G = nx.Graph()
    for feat in feature_list:
        G.add_node(feat["shop_id"], group=feat["label_group"])

    edges_to_add = []
    for i in range(len(feature_list)):
        for j in range(i + 1, len(feature_list)):
            shop1 = feature_list[i]
            shop2 = feature_list[j]

            delay_sim = 1 - abs(shop1["avg_delay_score"] - shop2["avg_delay_score"])
            profit_sim = 1 - abs(shop1["avg_profit_similarity"] - shop2["avg_profit_similarity"])
            similarity = (delay_sim + profit_sim) / 2

            if similarity >= threshold:
                edges_to_add.append((shop1["shop_id"], shop2["shop_id"], similarity))

    edges_to_add.sort(key=lambda x: x[2], reverse=True)
    edges_to_add = edges_to_add[:200]
    for u, v, w in edges_to_add:
        G.add_edge(u, v, weight=w)

    communities = list(greedy_modularity_communities(G))
    color_map = plt.get_cmap("tab20", len(communities))
    group_colors = {}
    unique_groups = sorted(set(f["label_group"] for f in feature_list))
    for idx, grp in enumerate(unique_groups):
        group_colors[grp] = color_map(idx)

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(14, 10))
    for idx, com in enumerate(communities):
        nx.draw_networkx_nodes(G, pos, nodelist=list(com), node_color=[group_colors.get(G.nodes[n]['group'], (0.5, 0.5, 0.5)) for n in com], label=f"Group {idx+1}", node_size=80)
    weights = [G[u][v]['weight'] for u,v in G.edges()]
    nx.draw_networkx_edges(G, pos, alpha=0.4, width=weights)
    nx.draw_networkx_labels(G, pos, font_size=7)
    plt.title("Shop Similarity Graph (Thresholded)")
    plt.legend()
    plt.tight_layout()
    plt.show()
def save_features_to_csv(feature_list, path="shop_features.csv"):
    df = pd.DataFrame(feature_list)
    df.to_csv(path, index=False)
    print(f"Özellikler CSV olarak kaydedildi: {path}")
def main():
    shop_files = glob(os.path.join(SHOP_DATA_DIR, "Shop *.json"))
    all_shops_product_days = {}
    all_shops_profit = {}
    for shop_file in shop_files:
        shop_id = int(os.path.basename(shop_file).split()[1].split(".")[0])
        full = extract_product_price_history(shop_file)
        all_shops_product_days[shop_id] = {k: [x for x in v] for k, v in full.items()}
        all_shops_profit[shop_id] = full

    args = [(shop_file, all_shops_product_days, all_shops_profit) for shop_file in shop_files]

    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        feature_list = pool.map(extract_shop_features_parallel, args)

    print("Toplam kayıt sayısı:", len(feature_list))
    for row in feature_list[:10]:
        print(row)
    save_features_to_csv(feature_list)


    # visualize_similarity_graph(feature_list, threshold=0.99)

if __name__ == "__main__":
    main()
