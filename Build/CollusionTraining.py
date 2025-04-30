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
    'Shop 48', 'Shop 58', 'Shop 219', 'Shop 318', 'Shop 141', 'Shop 122', 'Shop 198', 'Shop 106',
    'Shop 235', 'Shop 83', 'Shop 40', 'Shop 388', 'Shop 226', 'Shop 256', 'Shop 15', 'Shop 269',
    'Shop 233', 'Shop 340', 'Shop 3', 'Shop 165', 'Shop 71', 'Shop 41', 'Shop 125', 'Shop 307',
    'Shop 303', 'Shop 353', 'Shop 103', 'Shop 268', 'Shop 28', 'Shop 7', 'Shop 297', 'Shop 298',
    'Shop 357', 'Shop 400', 'Shop 73', 'Shop 34', 'Shop 230', 'Shop 241', 'Shop 55', 'Shop 21',
    'Shop 107', 'Shop 47', 'Shop 39', 'Shop 300', 'Shop 206', 'Shop 282', 'Shop 306', 'Shop 382',
    'Shop 262', 'Shop 120', 'Shop 258', 'Shop 348', 'Shop 384', 'Shop 363', 'Shop 11', 'Shop 360',
    'Shop 98', 'Shop 54', 'Shop 96', 'Shop 138', 'Shop 37', 'Shop 65', 'Shop 121', 'Shop 177',
    'Shop 231', 'Shop 304', 'Shop 315', 'Shop 104', 'Shop 331', 'Shop 69', 'Shop 44', 'Shop 84',
    'Shop 186', 'Shop 30', 'Shop 29', 'Shop 12', 'Shop 334', 'Shop 146', 'Shop 175', 'Shop 332',
    'Shop 62', 'Shop 378', 'Shop 170', 'Shop 162', 'Shop 9', 'Shop 319', 'Shop 199', 'Shop 154',
    'Shop 309', 'Shop 85', 'Shop 227', 'Shop 317', 'Shop 51', 'Shop 211', 'Shop 204', 'Shop 359',
    'Shop 172', 'Shop 115', 'Shop 322', 'Shop 223', 'Shop 383', 'Shop 320', 'Shop 224', 'Shop 90',
    'Shop 123', 'Shop 327', 'Shop 275', 'Shop 386', 'Shop 50', 'Shop 341', 'Shop 336', 'Shop 287',
    'Shop 312', 'Shop 355', 'Shop 394', 'Shop 399', 'Shop 276', 'Shop 361', 'Shop 285', 'Shop 97',
    'Shop 215', 'Shop 274', 'Shop 243', 'Shop 366', 'Shop 81', 'Shop 325', 'Shop 2', 'Shop 78',
    'Shop 210', 'Shop 279', 'Shop 13', 'Shop 169', 'Shop 196', 'Shop 291', 'Shop 305', 'Shop 128',
    'Shop 171', 'Shop 217', 'Shop 294', 'Shop 295', 'Shop 257', 'Shop 63', 'Shop 374', 'Shop 118',
    'Shop 157', 'Shop 136', 'Shop 333', 'Shop 266', 'Shop 321', 'Shop 248', 'Shop 8', 'Shop 272',
    'Shop 38', 'Shop 179', 'Shop 160', 'Shop 102', 'Shop 117', 'Shop 135', 'Shop 385', 'Shop 280',
    'Shop 72', 'Shop 207', 'Shop 99', 'Shop 174', 'Shop 364', 'Shop 5', 'Shop 89', 'Shop 23',
    'Shop 313', 'Shop 236', 'Shop 187', 'Shop 316', 'Shop 205', 'Shop 368', 'Shop 292', 'Shop 337',
    'Shop 209', 'Shop 100', 'Shop 133', 'Shop 137', 'Shop 376', 'Shop 380', 'Shop 52', 'Shop 24',
    'Shop 19', 'Shop 64', 'Shop 252', 'Shop 80', 'Shop 278', 'Shop 158', 'Shop 93', 'Shop 208',
    'Shop 349', 'Shop 293', 'Shop 222', 'Shop 113', 'Shop 130', 'Shop 220', 'Shop 250', 'Shop 390'
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
joblib.dump(model, "../Models/collusion_model15.pkl")
print("✅ Model başarıyla ./Models/collusion_model15.pkl olarak kaydedildi.")
