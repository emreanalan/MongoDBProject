import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import random

# CSV'den veri yükle
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv")

# Aykırı değerleri filtrele
df_filtered = df[(df['avg_price_similarity'] > 0.1) & (df['top_k_neighbor_overlap'] > 0.1)]

# Kümeleme için kullanılacak özellikler
features = [
    "avg_price_similarity",
    "top_k_neighbor_overlap",
    "price_std_similarity",
    "productwise_variance_across_shops",
    "profit_pct_std"
]

X = df_filtered[features].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# KMeans kümeleme
kmeans = KMeans(n_clusters=30, random_state=42)  # 30 grup
df_filtered["cluster"] = kmeans.fit_predict(X_scaled)

# Kümeler ve Collusion Gruplarını ilişkilendiren bir tablo oluşturma
collusion_group_to_cluster = {}

# Her küme için collusion_group'ları analiz et
for cluster_num in range(30):
    group_shops = df_filtered[df_filtered["cluster"] == cluster_num]["shop_id"].values
    print(f"Cluster {cluster_num}: Shop IDs: {group_shops}")

    cluster_matches = []
    for collusion_group_num, collusion_shops in COLLUSION_GROUPS.items():
        matching_shops = set(group_shops) & set(collusion_shops)
        if matching_shops:
            cluster_matches.append(f"Matches with Collusion Group {collusion_group_num}: {matching_shops}")

    collusion_group_to_cluster[cluster_num] = cluster_matches
    print("\n".join(cluster_matches))

# 1️⃣ PCA ile boyut indirgeme ve çizim
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
df_filtered["PCA1"] = X_pca[:, 0]
df_filtered["PCA2"] = X_pca[:, 1]

# Görselleştirme 1: PCA ile kümeleme
plt.figure(figsize=(10, 8))
scatter = plt.scatter(df_filtered["PCA1"], df_filtered["PCA2"], c=df_filtered["cluster"], cmap="tab20b")
plt.title("Shop Clusters (PCA Projection) with 30 Groups")
plt.xlabel("PCA 1")
plt.ylabel("PCA 2")
plt.legend(*scatter.legend_elements(), title="Cluster")
plt.grid(True)
plt.tight_layout()
plt.show()

# 2️⃣ Önemli 2 özellik ile çizim (zoom'lu)
plt.figure(figsize=(10, 8))
scatter2 = plt.scatter(
    df_filtered["avg_price_similarity"],
    df_filtered["top_k_neighbor_overlap"],
    c=df_filtered["cluster"],
    cmap="tab20b"
)
plt.title("Shop Clusters (AvgPriceSim vs NeighborOverlap) with 30 Groups")
plt.xlabel("Avg Price Similarity")
plt.ylabel("Top-K Neighbor Overlap")
plt.xlim(0.9, 1.0)
plt.ylim(0.6, 1.0)
plt.legend(*scatter2.legend_elements(), title="Cluster")
plt.grid(True)
plt.tight_layout()
plt.show()

# COLLUSION_GROUPS tanımından shop_id'leri al
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

# 3️⃣ Grupları yazdırma ve COLLUSION_GROUPS ile karşılaştırma

for cluster_num in range(30):
    print(f"Cluster {cluster_num}:")
    for match in collusion_group_to_cluster[cluster_num]:
        print(f"  - {match}")
    print()