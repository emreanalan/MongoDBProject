import os
import pymongo
import joblib
import numpy as np
import pandas as pd
from tabulate import tabulate
from sklearn.metrics import classification_report, accuracy_score

# === Feature Engineering Fonksiyonunu Çağır ===
from utils.feature_engineering import extract_features_from_shop

# === MongoDB Bağlantısı ===
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# === Test Shopları ===
normal_shops = [f"Shop {i}" for i in range(341, 371)]
collusion_shops = [f"Shop {i}" for i in range(371, 401)]

test_shops = normal_shops + collusion_shops
y_true = [0] * len(normal_shops) + [1] * len(collusion_shops)

# === Model Yükle ===
model = joblib.load("../Models/collusion_model.pkl")  # Düzeltildi: doğru Models klasör yolu

# === Test Verisi Hazırlama ===
X_test = []
valid_shops = []

for shop in test_shops:
    collection = db[shop]
    docs = list(collection.find({}, {"_id": 0}))
    features = extract_features_from_shop(docs)
    if features:
        X_test.append(features)
        valid_shops.append(shop)
    else:
        print(f"⚠️ {shop} için veri bulunamadı, atlanıyor.")

X_test = np.array(X_test)

# === Tahmin Yap ===
y_pred = model.predict(X_test)

# === Sonuçları Tablo Olarak Göster ===
results = []

for shop, pred in zip(valid_shops, y_pred):
    label = "✅ Normal" if pred == 0 else "🚨 Collusion"
    results.append([shop, label])

results_df = pd.DataFrame(results, columns=["Shop Name", "Prediction"])

print("\n=== Tahmin Tablosu ===")
print(tabulate(results_df, headers='keys', tablefmt='pretty', showindex=True))

# === Performans Değerlendirmesi ===
if len(y_true) == len(y_pred):
    print("\n=== Performans Raporu ===")
    print(f"🎯 Accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print(classification_report(y_true, y_pred))
else:
    print("\n⚠️ Gerçek label sayısı ile tahmin edilen label sayısı eşleşmedi!")
