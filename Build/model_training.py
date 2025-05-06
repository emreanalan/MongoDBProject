import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns


# 1. Veri yükleme
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv")

# 2. Veri temizleme ve özelliklerin hazırlanması
# 'shop_id' gibi gereksiz sütunları düşürebiliriz (modeli etkilememeli)
df = df.drop(columns=['shop_id'])

# 'is_collusion' ve 'collusion_group' hedef değişkenleridir.
X = df.drop(columns=['is_collusion', 'collusion_group'])
y = df['collusion_group']

# 3. Eğitim ve test verisi olarak ayırma (80% eğitim, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Modeli oluşturma (RandomForestClassifier örneği)
model = RandomForestClassifier(n_estimators=100, random_state=42)

# 5. Modeli eğitim verisiyle eğitme
model.fit(X_train, y_train)

# 6. Modelle tahmin yapma
y_pred = model.predict(X_test)

# 7. Modelin performansını değerlendirme
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_pred)

# 8. Confusion Matrix görselleştirmesi
plt.figure(figsize=(10,7))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=model.classes_, yticklabels=model.classes_)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

# 9. Özellik önemlerini görselleştirme (modelin en önemli özellikleri)
feature_importances = model.feature_importances_
sorted_idx = feature_importances.argsort()

plt.figure(figsize=(10,6))
plt.barh(X.columns[sorted_idx], feature_importances[sorted_idx])
plt.xlabel('Feature Importance')
plt.title('Feature Importance Ranking')
plt.show()

# 10. Test verisi üzerinde tahmin edilen grupların shop_id'leriyle birlikte birleştirilmesi
test_results = X_test.copy()
test_results['predicted_collusion_group'] = y_pred
test_results['actual_collusion_group'] = y_test  # Gerçek grubu ekleyelim

# Eğer orijinal df'de shop_id varsa, onu tekrar test sonuçlarına ekleyebilirsiniz
# Bu satırı df'nin içerdiği shop_id sütununa göre düzenleyebilirsiniz:
# test_results['shop_id'] = df.iloc[X_test.index]['shop_id']

# 11. Sonuçları gösterme
print("\nTest Verisi Üzerindeki Tahmin Sonuçları:")
print(test_results[['predicted_collusion_group', 'actual_collusion_group']])

# 12. Cluster shops: Tahmin edilen gruplara göre mağazaları kümelere ayırma
def cluster_shops(test_results):
    grouped_shops = test_results.groupby('predicted_collusion_group')['predicted_collusion_group'].count()
    print("\nTahmin Edilen Collusion Grupları ve İçlerindeki Mağazalar:")
    for group, count in grouped_shops.items():
        shops_in_group = test_results[test_results['predicted_collusion_group'] == group]
        print(f"Group {group} (Total Shops: {count}):")
        print(shops_in_group[['actual_collusion_group', 'predicted_collusion_group']])  # Hem gerçek hem de tahmin edilen grup bilgisi
        print("-" * 50)

# 13. Cluster sonuçlarını yazdırma
cluster_shops(test_results)

# 14. Modeli kaydetme (isteğe bağlı, ileriye dönük yeniden kullanma için)
import joblib
# joblib.dump(model, '../DataSetModels/collusion_model3.pkl')


from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

# 15. Cluster bazlı değerlendirme metrikleri
ari_score = adjusted_rand_score(y_test, y_pred)
nmi_score = normalized_mutual_info_score(y_test, y_pred)

print(f"\nAdjusted Rand Index (ARI): {ari_score:.4f}")
print(f"Normalized Mutual Information (NMI): {nmi_score:.4f}")
