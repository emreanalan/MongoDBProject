import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from collections import defaultdict

# Veri yolu
DATA_PATH = "/utils/shop_features3.csv"
df = pd.read_csv(DATA_PATH)

# 1. AŞAMA: Collusion var mı yok mu (Binary Classification)
features = [
    "price_change_count", "avg_day_between_changes", "manufacturer_count",
    "avg_profit_pct", "profit_pct_std", "product_count",
    "avg_delay_score", "exact_overlap_ratio", "avg_profit_similarity"
]

X = df[features]
y_binary = df["label_binary"]

X_train_bin, X_test_bin, y_train_bin, y_test_bin = train_test_split(X, y_binary, test_size=0.25, random_state=42)

clf_bin = RandomForestClassifier(n_estimators=100, random_state=42)
clf_bin.fit(X_train_bin, y_train_bin)

# Binary tahmin
y_pred_bin = clf_bin.predict(X_test_bin)
print("--- Classification Report (Binary) ---")
print(classification_report(y_test_bin, y_pred_bin))

cm_bin = confusion_matrix(y_test_bin, y_pred_bin)
sns.heatmap(cm_bin, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix - Binary Collusion Detection")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# Özellik önem dereceleri (Binary Model)
print("\n📌 Feature Importances (Binary Classification):")
importances_bin = clf_bin.feature_importances_
for feat, imp in sorted(zip(features, importances_bin), key=lambda x: -x[1]):
    print(f"{feat}: {imp:.4f}")

# 2. AŞAMA: Collusion olanları tahmine göre al
df["pred_binary"] = clf_bin.predict(X)
predicted_collusion_df = df[df["pred_binary"] == 1]

X_group = predicted_collusion_df[features]
y_group = predicted_collusion_df["label_group"]

X_train_grp, X_test_grp, y_train_grp, y_test_grp = train_test_split(X_group, y_group, test_size=0.25, random_state=42)

clf_grp = RandomForestClassifier(n_estimators=100, random_state=42)
clf_grp.fit(X_train_grp, y_train_grp)

# Grup tahmin
y_pred_grp = clf_grp.predict(X_test_grp)
print("--- Classification Report (Group) ---")
print(classification_report(y_test_grp, y_pred_grp, zero_division=0))

cm_grp = confusion_matrix(y_test_grp, y_pred_grp, labels=sorted(y_group.unique()))
sns.heatmap(cm_grp, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix - Collusion Group Classification")
plt.xlabel("Predicted label")
plt.ylabel("True label")
plt.xticks(ticks=np.arange(len(y_group.unique())), labels=sorted(y_group.unique()))
plt.yticks(ticks=np.arange(len(y_group.unique())), labels=sorted(y_group.unique()))
plt.show()

# Özellik önem dereceleri (Group Model)
print("\n📌 Feature Importances (Group Classification):")
importances_grp = clf_grp.feature_importances_
for feat, imp in sorted(zip(features, importances_grp), key=lambda x: -x[1]):
    print(f"{feat}: {imp:.4f}")

# Sonuçları listele
print("\n✅ Detected Normal Shops:")
print(df[df["pred_binary"] == 0]["shop_id"].values)

print("\n✅ Detected Collusion Shops:")
print(predicted_collusion_df["shop_id"].values)

print("\n📊 Collusion Group Matching:")
group_results = pd.DataFrame({
    "Shop ID": predicted_collusion_df["shop_id"],
    "Actual Group": predicted_collusion_df["label_group"],
    "Predicted Group": clf_grp.predict(X_group)
})
print(group_results.sort_values("Actual Group"))

print("\n📦 Collusion Group Product Analysis (Advanced):\n")
grouped = predicted_collusion_df.groupby("label_group")

# Bu kısmın çalışması için ürün bazlı fiyat verisine ihtiyaç var:
# shop_id -> product_id -> zaman serisi (fiyat + tarih) şeklinde erişilebilen bir yapı
# Örnek varsayım: her shop için ayrı bir CSV veya JSON içinde fiyat geçmişi var
# Şu anlık simüle ettiğim yapıda çalışırsa ana yapıyı entegre ederiz

# Bu sözlük, her grubun ürün analiz çıktısını saklar
collusion_group_results = {}

for group_id, group_df in grouped:
    shop_ids = group_df["shop_id"].tolist()
    print(f"🧠 Grup {group_id} - Shoplar: {shop_ids}")

    # Ortak ürünleri bulmak için ürün kümelerini kesiştir
    product_sets = []
    for shop_id in shop_ids:
        shop_row = df[df["shop_id"] == shop_id]
        if "product_list" in shop_row.columns:
            try:
                products = eval(shop_row.iloc[0]["product_list"])
                product_sets.append(set(products))
            except:
                continue

    if not product_sets:
        print("   ⚠️ Hiçbir shop için ürün bilgisi bulunamadı.")
        continue

    # Ortak ürünler
    common_products = set.intersection(*product_sets)
    print(f"   🔍 Ortak ürün sayısı: {len(common_products)}")

    # Collusion davranışı gösteren ürünleri filtrele (zam günü, oranı vs. simüle edilmiş kontrol)
    # Örnek: Her ürünün fiyat geçmişini bir dict’ten al (örn. price_history_dict)
    # price_history_dict: { shop_id: { product_id: [(day, price), ...] } }

    # Gerçekçi test verin varsa bunu buraya bağlayabiliriz
    # Şimdilik sadece common ürünleri döndürüyoruz
    collusion_group_results[f"group_{group_id}"] = {
        "shops": shop_ids,
        "collusion_products": list(common_products)
    }

    if common_products:
        print("   🎯 Ortak Collusion Ürünleri:")
        for pname in sorted(common_products):
            print(f"     🔸 {pname}")
    else:
        print("   ⚠️ Ortak collusion ürün bulunamadı.")
    print()


# Model kayıt
joblib.dump(clf_bin, "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Models/model_binary.pkl")
joblib.dump(clf_grp, "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Models/model_group.pkl")
