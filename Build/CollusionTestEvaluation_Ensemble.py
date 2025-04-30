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
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,  # 5 dakika
    socketTimeoutMS=600000,  # 10 dakika
    connectTimeoutMS=300000
)
db = client["DataSet"]

# === Test Shopları === #
# normal_shops = [f"Shop {i}" for i in range(341, 361)]
# collusion_shops = [f"Shop {i}" for i in range(361, 381)]
# normal_shops = [f"Shop {i}" for i in range(341, 361)] + [f"Shop {i}" for i in range(381, 391)]
# collusion_shops = [f"Shop {i}" for i in range(361, 381)] + [f"Shop {i}" for i in range(391, 401)]
# Collusion shops (lider + follower olanlar)
# Collusion Shops (Lider + Followerlar)
collusion_shops = {
    'Shop 52', 'Shop 97', 'Shop 84', 'Shop 29', 'Shop 23',
    'Shop 26', 'Shop 98', 'Shop 31',
    'Shop 19', 'Shop 87', 'Shop 11', 'Shop 49', 'Shop 32',
    'Shop 51', 'Shop 89', 'Shop 85', 'Shop 46', 'Shop 24',
    'Shop 64', 'Shop 59', 'Shop 68',
    'Shop 7', 'Shop 21', 'Shop 95', 'Shop 38', 'Shop 99',
    'Shop 76', 'Shop 27', 'Shop 17',
    'Shop 88', 'Shop 93', 'Shop 22', 'Shop 13',
    'Shop 90', 'Shop 82', 'Shop 77',
    'Shop 10', 'Shop 56', 'Shop 33', 'Shop 2', 'Shop 45',
    'Shop 4', 'Shop 28', 'Shop 41', 'Shop 8', 'Shop 5',
    'Shop 3', 'Shop 48', 'Shop 69', 'Shop 34'
}

# Normal Shops (logdan alınanlar)
normal_shops = {
    'Shop 12', 'Shop 86', 'Shop 91', 'Shop 57', 'Shop 70', 'Shop 18', 'Shop 6', 'Shop 37', 'Shop 75', 'Shop 72',
    'Shop 20', 'Shop 58', 'Shop 66', 'Shop 30', 'Shop 25', 'Shop 67', 'Shop 83', 'Shop 40', 'Shop 96', 'Shop 94',
    'Shop 61', 'Shop 100', 'Shop 42', 'Shop 73', 'Shop 9', 'Shop 60', 'Shop 54', 'Shop 71', 'Shop 63', 'Shop 79',
    'Shop 1', 'Shop 39', 'Shop 53', 'Shop 43', 'Shop 65', 'Shop 80', 'Shop 92', 'Shop 78', 'Shop 74', 'Shop 50',
    'Shop 47', 'Shop 16', 'Shop 15', 'Shop 62', 'Shop 36', 'Shop 14', 'Shop 35', 'Shop 55', 'Shop 81', 'Shop 44'
}


test_shops = list(normal_shops) + list(collusion_shops)
y_true = [0] * len(normal_shops) + [1] * len(collusion_shops)


# === 5 Modeli Yükle === #
model_paths = [
    "../Models/collusion_model.pkl",
    "../Models/collusion_model2.pkl",
    "../Models/collusion_model3.pkl",
    "../Models/collusion_model4.pkl",
    "../Models/collusion_model5.pkl",
    "../Models/collusion_model6.pkl",
    "../Models/collusion_model7.pkl",
    "../Models/collusion_model8.pkl",
    "../Models/collusion_model9.pkl",
    "../Models/collusion_model10.pkl",
    "../Models/collusion_model11.pkl",
    "../Models/collusion_model12.pkl",
    "../Models/collusion_model13.pkl",
    "../Models/collusion_model14.pkl",
    "../Models/collusion_model15.pkl"
]
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

all_preds = np.array(all_preds)  # Şekil: (5, num_samples)

# === Ensemble Kararı Ver: En az 3 model "Collusion" diyorsa → Collusion === #
final_preds = []

for i in range(all_preds.shape[1]):
    collusion_votes = np.sum(all_preds[:, i] == 1)
    final_label = 1 if collusion_votes >= 5 else 0
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
