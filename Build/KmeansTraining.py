import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Veri yükleme
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv")

# 2. Orijinal shop_id ve gerçek etiketleri koru
original_df = df[['shop_id', 'is_collusion', 'collusion_group']].copy()

# 3. Özellik seçimi (etiketleri çıkart)
X = df.drop(columns=['shop_id', 'is_collusion', 'collusion_group'])

# 4. KMeans modelini oluştur ve eğit (örnek: 20 cluster)
n_clusters = 7
model = KMeans(n_clusters=n_clusters, random_state=42)
cluster_labels = model.fit_predict(X)

# 5. Sonuçları birleştir
df['cluster_label'] = cluster_labels
df['shop_id'] = original_df['shop_id']
df['is_collusion'] = original_df['is_collusion']
df['collusion_group'] = original_df['collusion_group']

# 6. Sonuçları CSV olarak kaydet
df[['shop_id', 'cluster_label', 'is_collusion', 'collusion_group']].to_csv(
    "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/clustered1_shops.csv", index=False
)

print(f"\n✅ Clustering işlemi tamamlandı. Sonuçlar 'clustered_shops.csv' dosyasına yazıldı.")

# 7. Değerlendirme (varsa gerçek gruplarla kıyasla)
if 'collusion_group' in df.columns:
    ari = adjusted_rand_score(df['collusion_group'], df['cluster_label'])
    nmi = normalized_mutual_info_score(df['collusion_group'], df['cluster_label'])
    print(f"\n🔍 Değerlendirme Metrikleri:")
    print(f"Adjusted Rand Index (ARI): {ari:.4f}")
    print(f"Normalized Mutual Information (NMI): {nmi:.4f}")

# 8. Cluster içi özet tablo (her grupta kaç collusion var)
print("\n📊 Cluster bazlı collusion dağılımı:")
summary = df.groupby('cluster_label')['is_collusion'].value_counts().unstack().fillna(0)
print(summary)

# 9. İsteğe bağlı: Confusion benzeri ısı haritası
plt.figure(figsize=(10,6))
sns.heatmap(summary, annot=True, fmt=".0f", cmap="YlGnBu")
plt.title("Cluster'lara Göre Collusion Dağılımı")
plt.xlabel("is_collusion (0 = Normal, 1 = Collusion)")
plt.ylabel("Cluster Label")
plt.tight_layout()
plt.show()
