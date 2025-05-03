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
SIMILARITY_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_pair_similarities.csv"
OUTPUT_FEATURES_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features4.csv"

COLLUSION_GROUPS = {
    1: [356, 376, 309],
    2: [228, 192, 329, 258, 1],
    3: [199, 161, 38, 241],
    4: [395, 312, 76],
    5: [90, 164, 365, 62, 292],
    6: [320, 24, 121],
    7: [105, 335, 201, 364, 104],
    8: [73, 45, 232],
    9: [116, 379, 102],
    10: [372, 328, 371, 139, 265],
    11: [195, 82, 351, 304],
    12: [344, 375, 193],
    13: [290, 7, 175],
    14: [314, 129, 212, 211],
    15: [400, 41, 122, 217],
    16: [227, 9, 46, 3],
    17: [125, 293, 360],
    18: [243, 361, 268, 186],
    19: [79, 233, 12],
    20: [33, 368, 224],
    21: [10, 92, 174],
    22: [279, 315, 58, 282],
    23: [169, 387, 246, 142, 155],
    24: [382, 296, 188],
    25: [160, 322, 327],
    26: [319, 99, 352],
    27: [338, 159, 263, 242],
    28: [185, 394, 348, 4],
    29: [110, 277, 367, 366],
    30: [69, 240, 61],
    31: [396, 36, 248],
    32: [198, 255, 321, 317],
    33: [189, 231, 114],
    34: [299, 278, 131, 17],
    35: [55, 96, 21],
    36: [177, 218, 83, 187, 208],
    37: [383, 285, 330, 134, 143],
    38: [275, 108, 95, 388, 345],
    39: [89, 44, 85],
    40: [283, 310, 16, 88],
    41: [179, 264, 149, 205],
    42: [84, 254, 247],
    43: [26, 168, 19],
    44: [308, 359, 138],
    45: [194, 257, 291],
    46: [115, 70, 14],
    47: [39, 350, 397, 234, 146],
    48: [135, 343, 32, 150, 101],
    49: [377, 165, 137, 147],
    50: [162, 23, 286, 6, 386],
    51: [27, 362, 173],
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

def build_similarity_lookup(sim_df):
    lookup = defaultdict(dict)
    for _, row in sim_df.iterrows():
        id1, id2 = int(row["shop_id_1"]), int(row["shop_id_2"])
        data = (row["delay_score"], row["overlap_score"], row["profit_similarity"])
        lookup[id1][id2] = data
        lookup[id2][id1] = data  # iki yönlü ekle
    return lookup

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

def extract_shop_features(shop_path, similarity_lookup):
    shop_id = int(os.path.basename(shop_path).split()[1].split(".")[0])
    product_days = extract_product_price_history(shop_path)

    # Temel istatistikler
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

    # Zaman aralıkları
    sorted_dates = sorted(all_dates)
    date_objs = [datetime.strptime(d, "%Y-%m-%d") for d in sorted_dates]
    date_diffs = np.diff(sorted(date_objs))
    day_intervals = [d.days for d in date_diffs]

    # Diğer mağazalara göre ortalama similarity değerleri
    similarities = similarity_lookup.get(shop_id, {})
    delays, overlaps, profits = zip(*similarities.values()) if similarities else ([], [], [])
    avg_delay_score = np.mean(delays) if delays else 0
    exact_overlap_ratio = np.mean(overlaps) if overlaps else 0
    avg_profit_similarity = np.mean(profits) if profits else 0

    # Grup içi benzerlikler
    group_id = COLLUSION_SHOPS.get(shop_id, -1)
    group_shops = COLLUSION_GROUPS.get(group_id, [])
    group_delays, group_overlaps, group_profits = [], [], []
    shared_products = []

    for other_id in group_shops:
        if other_id == shop_id or other_id not in similarities:
            continue
        d, o, p = similarities[other_id]
        group_delays.append(d)
        group_overlaps.append(o)
        group_profits.append(p)

        # Shared product count
        shared = set(product_days.keys()) & set(similarity_lookup.get(other_id, {}).keys())
        shared_products.append(len(shared))

    return {
        "shop_id": shop_id,
        "price_change_count": len(all_dates),
        "avg_day_between_changes": np.mean(day_intervals) if day_intervals else 0,
        "manufacturer_count": len(manufacturer_set),
        "avg_profit_pct": np.mean(profit_percentages) if profit_percentages else 0,
        "profit_pct_std": np.std(profit_percentages) if profit_percentages else 0,
        "product_count": len(product_days),
        "avg_delay_score": avg_delay_score,
        "exact_overlap_ratio": exact_overlap_ratio,
        "avg_profit_similarity": avg_profit_similarity,
        "group_size": len(group_shops),
        "group_avg_delay_score": np.mean(group_delays) if group_delays else 0,
        "group_avg_overlap_ratio": np.mean(group_overlaps) if group_overlaps else 0,
        "group_avg_profit_similarity": np.mean(group_profits) if group_profits else 0,
        "shared_products_with_group": np.mean(shared_products) if shared_products else 0,
        "label_binary": 1 if shop_id in COLLUSION_SHOPS else 0,
        "label_group": group_id
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
def save_features_to_csv(feature_list, path="shop_features4.csv"):
    df = pd.DataFrame(feature_list)
    df.to_csv(path, index=False)
    print(f"Özellikler CSV olarak kaydedildi: {path}")
def main():
    sim_df = pd.read_csv(SIMILARITY_CSV)
    similarity_lookup = build_similarity_lookup(sim_df)

    shop_files = glob(os.path.join(SHOP_DATA_DIR, "Shop *.json"))
    features = [extract_shop_features(f, similarity_lookup) for f in shop_files]

    df = pd.DataFrame(features)
    df.to_csv(OUTPUT_FEATURES_CSV, index=False)
    print(f"Özellik dosyası kaydedildi: {OUTPUT_FEATURES_CSV}")

if __name__ == "__main__":
    main()
