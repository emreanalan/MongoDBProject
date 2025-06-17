import pymongo
import json
import os
from datetime import datetime


# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,
    socketTimeoutMS=600000,
    connectTimeoutMS=300000
)
db = client["DataSet"]

# Kayıtları dışa aktarmak istediğin shop isimleri
shop_names = [f"Shop {i}" for i in range(1, 401)]

# Çıktı klasörü
os.makedirs("exported_shops3", exist_ok=True)

def convert_datetime(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")
    return obj

for shop in shop_names:
    cursor = db[shop].find({}, {"_id": 0})
    data = list(cursor)

    with open(f"exported_shops3/{shop}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=convert_datetime)

    print(f"✅ {shop} verisi exported!")
