import pymongo
from datetime import datetime
from bson import ObjectId

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

db = client["DataSet"]


# Belgeler ve koleksiyon eşleştirmeleri
data_to_insert = [
    {
        "collection": "DogalGaz",
        "document": {
            "_id": ObjectId("67e3d3e214a6317cb6a17995"),
            "title": "100m^3 için Doğalgaz fiyatı 2025",
            "Date": datetime(2025, 1, 1),
            "Price": "1362.1 TL"
        }
    },
    {
        "collection": "Elektrik",
        "document": {
            "_id": ObjectId("67e3d48c682e75bf8eb960da"),
            "title": "Tüm Vergi ve Fonlar Dahil Son Fiyat (TL/kWh) 2025",
            "Date": datetime(2025, 1, 1),
            "Price": "4.48 TL"
        }
    },
    {
        "collection": "Asgari_Ucret",
        "document": {
            "_id": ObjectId("67e3d2da5405a739d06d746a"),
            "title": "NET ASGARİ ÜCRET",
            "Date": datetime(2025, 1, 1),
            "Price": "22,104.67 TL"
        }
    }
]

# Verileri ilgili koleksiyonlara ekle
for item in data_to_insert:
    collection = db[item["collection"]]
    try:
        collection.insert_one(item["document"])
        print(f"{item['document']['title']} -> {item['collection']} koleksiyonuna eklendi.")
    except pymongo.errors.DuplicateKeyError:
        print(f"{item['document']['title']} zaten mevcut, atlandı.")

print("Tüm veri ekleme işlemleri tamamlandı.")
