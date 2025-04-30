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
collusion_Shops = {
    'Shop 201', 'Shop 159', 'Shop 60',
    'Shop 43', 'Shop 367', 'Shop 327', 'Shop 309', 'Shop 48',
    'Shop 47', 'Shop 336', 'Shop 71', 'Shop 54',
    'Shop 180', 'Shop 271', 'Shop 250', 'Shop 200',
    'Shop 328', 'Shop 374', 'Shop 82', 'Shop 260', 'Shop 168',
    'Shop 232', 'Shop 88', 'Shop 255', 'Shop 305', 'Shop 274',
    'Shop 74', 'Shop 10', 'Shop 181', 'Shop 145',
    'Shop 268', 'Shop 360', 'Shop 329', 'Shop 142',
    'Shop 372', 'Shop 316', 'Shop 90', 'Shop 223', 'Shop 345',
    'Shop 219', 'Shop 344', 'Shop 216', 'Shop 258', 'Shop 126',
    'Shop 123', 'Shop 398', 'Shop 61',
    'Shop 311', 'Shop 39', 'Shop 66',
    'Shop 150', 'Shop 188', 'Shop 21', 'Shop 364',
    'Shop 246', 'Shop 187', 'Shop 179', 'Shop 59',
    'Shop 124', 'Shop 87', 'Shop 58', 'Shop 240',
    'Shop 211', 'Shop 222', 'Shop 343', 'Shop 257', 'Shop 399',
    'Shop 156', 'Shop 20', 'Shop 325',
    'Shop 15', 'Shop 53', 'Shop 347', 'Shop 197',
    'Shop 315', 'Shop 375', 'Shop 265', 'Shop 147',
    'Shop 288', 'Shop 160', 'Shop 342', 'Shop 365',
    'Shop 220', 'Shop 44', 'Shop 8', 'Shop 57',
    'Shop 194', 'Shop 294', 'Shop 38',
    'Shop 9', 'Shop 248', 'Shop 300', 'Shop 228', 'Shop 218',
    'Shop 73', 'Shop 361', 'Shop 312', 'Shop 95', 'Shop 132',
    'Shop 83', 'Shop 131', 'Shop 247', 'Shop 100',
    'Shop 358', 'Shop 207', 'Shop 283', 'Shop 55',
    'Shop 85', 'Shop 321', 'Shop 253', 'Shop 242', 'Shop 129',
    'Shop 27', 'Shop 34', 'Shop 282',
    'Shop 153', 'Shop 6', 'Shop 63', 'Shop 215',
    'Shop 196', 'Shop 4', 'Shop 393', 'Shop 97',
    'Shop 203', 'Shop 5', 'Shop 29', 'Shop 377', 'Shop 26',
    'Shop 378', 'Shop 386', 'Shop 56', 'Shop 146', 'Shop 33',
    'Shop 2', 'Shop 176', 'Shop 272', 'Shop 78',
    'Shop 140', 'Shop 314', 'Shop 381', 'Shop 356',
    'Shop 167', 'Shop 183', 'Shop 86', 'Shop 350',
    'Shop 143', 'Shop 138', 'Shop 116',
    'Shop 217', 'Shop 346', 'Shop 395',
    'Shop 52', 'Shop 302', 'Shop 186', 'Shop 162',
    'Shop 144', 'Shop 121', 'Shop 391', 'Shop 50',
    'Shop 169', 'Shop 135', 'Shop 339',
    'Shop 297', 'Shop 202', 'Shop 351',
    'Shop 278', 'Shop 170', 'Shop 25', 'Shop 221', 'Shop 105',
    'Shop 24', 'Shop 94', 'Shop 210',
    'Shop 209', 'Shop 362', 'Shop 286', 'Shop 333', 'Shop 37',
    'Shop 62', 'Shop 319', 'Shop 226', 'Shop 280', 'Shop 384',
    'Shop 98', 'Shop 99', 'Shop 236', 'Shop 249', 'Shop 166',
    'Shop 81', 'Shop 290', 'Shop 270',
    'Shop 259', 'Shop 112', 'Shop 172', 'Shop 273', 'Shop 42',
    'Shop 373', 'Shop 313', 'Shop 353', 'Shop 118'
}


shop_names = [f"Shop {i}" for i in range(1, 401)]
X = []
y = []

for shop in shop_names:
    collusion_label = 1 if shop in collusion_Shops else 0  # Etiketi collusion setine göre ata
    collection = db[shop]
    docs = list(collection.find({}, {"_id": 0}))

    if docs:
        feature_vector = extract_features_from_shop(docs)
        X.append(feature_vector)
        y.append(collusion_label)



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
joblib.dump(model, "../Models/collusion_model12.pkl")
print("✅ Model başarıyla ./Models/collusion_model12.pkl olarak kaydedildi.")
