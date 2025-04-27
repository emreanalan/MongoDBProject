import os
import pymongo
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Yeni eklenen feature engineering fonksiyonumuz
from utils.feature_engineering import extract_features_from_shop

# === MongoDB Bağlantısı === #
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# === Shopları Yükle === #
shop_names = [f"Shop {i}" for i in range(1, 341)]  # 1-340 arası
X = []
y = []

for shop in shop_names:
    collusion_label = 1 if int(shop.split()[1]) >= 171 else 0  # 171-340 arası collusion
    collection = db[shop]
    docs = list(collection.find({}, {"_id": 0}))  # Dökümanları liste olarak çekiyoruz

    if docs:
        feature_vector = extract_features_from_shop(docs)
        X.append(feature_vector)
        y.append(collusion_label)

# === Shopları Yükle === #
# shop_names = [f"Shop {i}" for i in range(1, 341)]  # 1-340 arası hepsi
# X = []
# y = []
#
# for shop in shop_names:
#     shop_num = int(shop.split()[1])
#     collusion_label = 1 if shop_num >= 44 else 0  # 44 ve sonrası collusion
#     collection = db[shop]
#     docs = list(collection.find({}, {"_id": 0}))
#
#     if docs:
#         feature_vector = extract_features_from_shop(docs)
#         X.append(feature_vector)
#         y.append(collusion_label)


# for shop in shop_names:
#     shop_num = int(shop.split()[1])
#     collusion_label = 1 if shop_num >= 298 else 0  # 298 ve sonrası collusion
#     collection = db[shop]
#     docs = list(collection.find({}, {"_id": 0}))
#
#     if docs:
#         feature_vector = extract_features_from_shop(docs)
#         X.append(feature_vector)
#         y.append(collusion_label)



# === Feature'ları ve Label'ları Ayır === #
X = np.array(X)
y = np.array(y)

print(f"📊 Toplam veri: {len(X)} örnek, {X.shape[1]} özellik")
print(f"📚 Pozitif label (Collusion) sayısı: {np.sum(y)}\n")

# === Train-Test Bölme === #
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# === Model Eğitimi === #
#model = RandomForestClassifier(n_estimators=200, random_state=42)
model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

# === Test Değerlendirme === #
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"✅ Test doğruluğu: {acc:.4f}")
print("📋 Classification Report:")
print(classification_report(y_test, y_pred))

# === Modeli Kaydet === #
os.makedirs("../Models", exist_ok=True)  # Models klasörü yoksa oluşturur
joblib.dump(model, "../Models/collusion_model6.pkl")
print("✅ Model başarıyla ./Models/collusion_model6.pkl olarak kaydedildi.")
