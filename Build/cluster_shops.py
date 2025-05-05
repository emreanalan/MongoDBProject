import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# Dosya yolu
FEATURE_CSV = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv"

# 1. Adım: Veriyi yükle
print("📂 Veriler yükleniyor...")
df = pd.read_csv(FEATURE_CSV)

# 2. Adım: İlişkisel (relational) özellikleri seç
relational_features = [
    'avg_profit_similarity',
    'exact_overlap_ratio',
    'avg_delay_score',
    'group_size',
    'group_avg_delay_score',
    'group_avg_overlap_ratio',
    'group_avg_profit_similarity',
    'shared_products_with_group'
]

X = df[relational_features]

# 3. Adım: Normalize et
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 4. Adım: Elbow yöntemi ile ideal küme sayısını belirle (isteğe bağlı görselleştirme)
print("📊 Elbow yöntemi uygulanıyor...")
inertias = []
k_range = range(2, 21)
for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)

# Elbow grafiği
plt.figure(figsize=(8, 4))
plt.plot(k_range, inertias, marker='o')
plt.title('Elbow Method for Optimal K')
plt.xlabel('Cluster Count (K)')
plt.ylabel('Inertia')
plt.grid(True)
plt.show()

# 5. Adım: Kümeleme
print("🤖 KMeans ile kümeleniyor...")
optimal_k = 80
kmeans = KMeans(n_clusters=optimal_k, random_state=42)
df['predicted_group'] = kmeans.fit_predict(X_scaled)

# 6. Adım: Grupları yazdır
print("\n🔍 Oluşturulan Kümeler:")
for group_id in sorted(df['predicted_group'].unique()):
    shops = df[df['predicted_group'] == group_id]['shop_id'].tolist()
    print(f"🧠 Grup {group_id + 1} - Shoplar: {shops}")

# 7. Adım: Sonuçları kaydet
output_path = FEATURE_CSV.replace(".csv", "_clustered.csv")
df.to_csv(output_path, index=False)
print(f"\n✅ Kümelenmiş veri kaydedildi: {output_path}")
