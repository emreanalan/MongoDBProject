import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

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
kmeans = KMeans(n_clusters=10, random_state=42)
df_filtered["cluster"] = kmeans.fit_predict(X_scaled)

# 1️⃣ PCA ile boyut indirgeme ve çizim
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
df_filtered["PCA1"] = X_pca[:, 0]
df_filtered["PCA2"] = X_pca[:, 1]

plt.figure(figsize=(8, 6))
scatter = plt.scatter(df_filtered["PCA1"], df_filtered["PCA2"], c=df_filtered["cluster"], cmap="tab10")
plt.title("Shop Clusters (PCA Projection)")
plt.xlabel("PCA 1")
plt.ylabel("PCA 2")
plt.legend(*scatter.legend_elements(), title="Cluster")
plt.grid(True)
plt.tight_layout()
plt.show()

# 2️⃣ Önemli 2 özellik ile çizim (zoom'lu)
plt.figure(figsize=(8, 6))
scatter2 = plt.scatter(
    df_filtered["avg_price_similarity"],
    df_filtered["top_k_neighbor_overlap"],
    c=df_filtered["cluster"],
    cmap="tab10"
)
plt.title("Shop Clusters (AvgPriceSim vs NeighborOverlap)")
plt.xlabel("Avg Price Similarity")
plt.ylabel("Top-K Neighbor Overlap")
plt.xlim(0.9, 1.0)
plt.ylim(0.6, 1.0)
plt.legend(*scatter2.legend_elements(), title="Cluster")
plt.grid(True)
plt.tight_layout()
plt.show()
