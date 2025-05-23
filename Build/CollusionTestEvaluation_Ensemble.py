import os
import pymongo
import joblib
import numpy as np
import pandas as pd
from tabulate import tabulate
from sklearn.metrics import classification_report, accuracy_score

# === Feature Engineering Fonksiyonunu Çağır ===
from utils.feature_engineering import extract_features_from_shop

# === MongoDB Bağlantısı === #
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# === Test Shopları === #
normal_shops = [f"Shop {i}" for i in range(341, 371)]
collusion_shops = [f"Shop {i}" for i in range(371, 401)]

test_shops = normal_shops + collusion_shops
y_true = [0] * len(normal_shops) + [1] * len(collusion_shops)

# === 5 Modeli Yükle ve Ağırlıklarını Belirle === #
model_paths = [
    "../Models/collusion_model.pkl",
    "../Models/collusion_model2.pkl",
    "../Models/collusion_model3.pkl",
    "../Models/collusion_model4.pkl",
    "../Models/collusion_model5.pkl",
]
model_weights = [1.0, 1.0, 1.0, 1.0, 1.0]  # 4. ve 5. modele daha fazla ağırlık verdik

models = [joblib.load(path) for path in model_paths]

# === Test Verisi Hazırlama === #
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

# === 5 Model ile Tahmin Yap === #
all_preds = []

for model in models:
    preds = model.predict(X_test)
    all_preds.append(preds)

all_preds = np.array(all_preds)  # (5, num_samples)

# === Ensemble Kararı Ver: Ağırlıklı Oylama Sistemi === #
final_preds = []

for i in range(all_preds.shape[1]):  # her shop için
    weighted_vote = 0.0
    for model_idx in range(len(models)):
        if all_preds[model_idx, i] == 1:
            weighted_vote += model_weights[model_idx]

    total_weight = sum(model_weights)
    threshold = total_weight / 2

    final_label = 1 if weighted_vote >= threshold else 0
    final_preds.append(final_label)

final_preds = np.array(final_preds)

# === Sonuçları Tablo Olarak Göster === #
results = []

for shop, pred in zip(valid_shops, final_preds):
    label = "✅ Normal" if pred == 0 else "🚨 Collusion"
    results.append([shop, label])

results_df = pd.DataFrame(results, columns=["Shop Name", "Prediction"])

print("\n=== Tahmin Tablosu ===")
print(tabulate(results_df, headers='keys', tablefmt='pretty', showindex=True))

# === Performans Değerlendirmesi === #
if len(y_true) == len(final_preds):
    print("\n=== Performans Raporu ===")
    print(f"🎯 Accuracy: {accuracy_score(y_true, final_preds):.4f}")
    print(classification_report(y_true, final_preds))
else:
    print("\n⚠️ Gerçek label sayısı ile tahmin edilen label sayısı eşleşmedi!")
