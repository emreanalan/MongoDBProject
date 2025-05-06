import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 1. Yeni test verisini yükleme
new_test_df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features2.csv")

# Özellikleri ve hedef değişkeni ayırma
X_new_test = new_test_df.drop(columns=['is_collusion', 'collusion_group', 'shop_id'])  # 'shop_id' varsa düşürebiliriz
y_new_test = new_test_df['collusion_group']

# 2. Önceden eğitilmiş modeli yükleme
model = joblib.load('../DataSetModels/collusion_model3.pkl')

# 3. Model ile tahmin yapma
y_pred_new_test = model.predict(X_new_test)

# 4. Performans değerlendirme
print("Yeni Test Verisi Accuracy:", accuracy_score(y_new_test, y_pred_new_test))

# Gerçek ve tahmin edilen sınıfları birleştirerek sadece kullanılan sınıfları al
used_labels = sorted(set(y_new_test).union(set(y_pred_new_test)))

print("\nYeni Test Verisi Classification Report:")
print(classification_report(y_new_test, y_pred_new_test, labels=used_labels))

print("\nYeni Test Verisi Confusion Matrix:")
cm_new_test = confusion_matrix(y_new_test, y_pred_new_test, labels=used_labels)

# Confusion Matrix görselleştirme
plt.figure(figsize=(12, 10))
sns.heatmap(cm_new_test, annot=True, fmt="d", cmap="Blues", xticklabels=used_labels, yticklabels=used_labels)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Yeni Test Verisi Confusion Matrix')
plt.tight_layout()
plt.show()

from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

# 15. Cluster bazlı değerlendirme metrikleri
ari_score = adjusted_rand_score(y_new_test, y_pred_new_test)
nmi_score = normalized_mutual_info_score(y_new_test, y_pred_new_test)

print(f"\nAdjusted Rand Index (ARI): {ari_score:.4f}")
print(f"Normalized Mutual Information (NMI): {nmi_score:.4f}")


# shop_id'leri geri eklemek için önce veriyi tekrar okuyalım
full_test_df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features2.csv")

# shop_id, gerçek ve tahmin edilen grup bilgilerini birleştirelim
comparison_df = pd.DataFrame({
    'shop_id': full_test_df['shop_id'],
    'actual_group': y_new_test,
    'predicted_group': y_pred_new_test
})

# Gruplara göre sıralayalım
comparison_df = comparison_df.sort_values(by=['actual_group', 'predicted_group']).reset_index(drop=True)

# CSV olarak kaydet (isteğe bağlı)
comparison_df.to_csv("predicted_vs_actual_collusion_groups.csv", index=False)

# Ekrana yazdıralım
print("\nTahmin Edilen vs Gerçek Collusion Grupları (Shop Bazında):")
print(comparison_df)


# Her gerçek grup için, hangi mağazaların nasıl tahmin edildiğini göster
grouped = comparison_df.groupby('actual_group')

print("\n🔍 Grup Bazlı Detaylı Karşılaştırma:")
for group_id, group_data in grouped:
    print(f"\nGerçek Grup {group_id} - Toplam {len(group_data)} mağaza:")
    print(group_data[['shop_id', 'actual_group', 'predicted_group']])


n_predicted_groups = len(set(y_pred_new_test))
print(f"Tahmin edilen farklı grup sayısı: {n_predicted_groups}")