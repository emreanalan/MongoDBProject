import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from DataRetrieval import fetch_all_manufacturers, fetch_shops_for_manufacturer, fetch_price_data_from_shop, \
    fetch_manufacturer_data
from ShopFeatureEngineering import create_shop_features

start_date = "2025-01-01"
end_date = "2025-04-20"

print("\n" + "=" * 60)
print("🛠️  === MODEL TRAINING STARTED ===")
print("=" * 60 + "\n")

X_all = []
y_all = []

manufacturers = fetch_all_manufacturers()

for manufacturer in manufacturers:
    shop_list = fetch_shops_for_manufacturer(manufacturer)

    if len(shop_list) < 2:
        print(f"[Warning] {manufacturer}: Yeterli shop bulunamadı, atlanıyor.\n")
        continue

    X, y = create_shop_features(shop_list, manufacturer, start_date, end_date, max_delay_days=7)

    if X is None or y is None:
        print(f"[Warning] {manufacturer}: Feature oluşturulamadı, atlanıyor.\n")
        continue

    X_all.append(X)
    y_all.append(y)

if not X_all:
    print("\n❌ Hiç feature bulunamadı. Eğitim iptal edildi.")
    exit()

# Tüm verileri birleştir
X_all = np.vstack(X_all)
y_all = np.concatenate(y_all)

# Eğitim / Test bölmesi
X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.2, random_state=42, stratify=y_all)

# Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Prediction
y_pred = model.predict(X_test)

# Skorlar
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)

print("\n" + "=" * 60)
print("📊 === MODEL EVALUATION RESULTS ===")
print("=" * 60)
print(f"🔵 Accuracy : {accuracy:.4f}")
print(f"🟢 Precision: {precision:.4f}")
print(f"🟠 Recall   : {recall:.4f}")
print(f"🟣 F1 Score : {f1:.4f}")
print("=" * 60 + "\n")

# Modeli kaydet
with open("shop_relation_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model başarıyla 'shop_relation_model.pkl' olarak kaydedildi.\n")

print("=" * 60)
print("🎯 === MODEL TRAINING COMPLETED ===")
print("=" * 60)
