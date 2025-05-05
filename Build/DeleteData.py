import pymongo
from datetime import datetime, timedelta

# MongoDB connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]


def delete_last_x_days(collection_name, days):
    collection = db[collection_name]

    cutoff_date = datetime.now() - timedelta(days=days)

    result = collection.delete_many({"Date": {"$gte": cutoff_date}})

    print(
        f"Deleted {result.deleted_count} records from '{collection_name}' that were inserted in the last {days} days.")


def delete_date_range(collection_name, start_date_str, end_date_str):
    collection = db[collection_name]
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    result = collection.delete_many({"Date": {"$gte": start_date, "$lte": end_date}})
    print(f"Deleted {result.deleted_count} records from '{collection_name}' between {start_date.date()} and {end_date.date()}.")



#delete_last_x_days("Copper/TRY", 20)
#delete_last_x_days("Aluminum/TRY", 20)
#delete_last_x_days("Silver/TRY", 20)
#delete_last_x_days("EUR/TRY", 20)
#delete_last_x_days("USD/TRY", 20)
#delete_last_x_days("Gold/TRY", 20)
# delete_date_range("IKEA", "2025-01-01", "2025-04-20")
# delete_date_range("A101", "2025-01-01", "2025-04-20")
# delete_date_range("MIGROS", "2025-01-01", "2025-04-20")
# delete_date_range("MediaMarkt", "2025-01-01", "2025-04-20")
# delete_date_range("Teknosa", "2025-01-01", "2025-04-20")
# delete_date_range("ToyMan", "2025-01-01", "2025-04-20")
# delete_date_range("KablocuAhmet", "2025-01-01", "2025-04-20")
# delete_date_range("ToyzSHop", "2025-01-01", "2025-04-20")
# delete_date_range("Vatan", "2025-01-01", "2025-04-20")
# delete_date_range("MyElectrician", "2025-01-01", "2025-04-20")
# delete_date_range("YourElectrician", "2025-01-01", "2025-04-20")
# delete_date_range("HisElectrician", "2025-01-01", "2025-04-20")
# delete_date_range("FraudShop", "2025-01-01", "2025-04-20")

##########################################################################
# Product 1'den Product 500'e kadar olan collectionları sil
# for i in range(1, 171):
#     collection_name = f"Shop {i}"
#     if collection_name in db.list_collection_names():
#         db.drop_collection(collection_name)
#         print(f"Collection '{collection_name}' silindi.")
#     else:
#         print(f"Collection '{collection_name}' bulunamadı, zaten yok.")
#
# print("Tüm Product collectionları başarıyla temizlendi!")
#
# for i in range(171, 341):
#     collection_name = f"Shop {i}"
#     if collection_name in db.list_collection_names():
#         db.drop_collection(collection_name)
#         print(f"Collection '{collection_name}' silindi.")
#     else:
#         print(f"Collection '{collection_name}' bulunamadı, zaten yok.")
#
# print("Tüm Product collectionları başarıyla temizlendi!")

for i in range(1,401):
    collection_name = f"Shop {i}"
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        print(f"Collection '{collection_name}' silindi.")
    else:
        print(f"Collection '{collection_name}' bulunamadı, zaten yok.")

print("Tüm Product collectionları başarıyla temizlendi!")

# for i in range(1, 26):
#     collection_name = f"Man {i}"
#     if collection_name in db.list_collection_names():
#         db.drop_collection(collection_name)
#         print(f"Collection '{collection_name}' silindi.")
#     else:
#         print(f"Collection '{collection_name}' bulunamadı, zaten yok.")
#
# print("Tüm Product collectionları başarıyla temizlendi!")
#################################################################################################

# man1_collection = db["Man1"]
#
# # Silmek istediğin ürün numaraları
# products_to_delete = [21, 22, 23, 24, 25]
#
# # Tüm kayıtları güncelle
# for doc in man1_collection.find():
#     update_fields = {}
#
#     for product_num in products_to_delete:
#         update_fields[f"Product {product_num}"] = ""
#         update_fields[f"Product {product_num} Price"] = ""
#
#     # Güncelleme işlemi
#     man1_collection.update_one(
#         {"_id": doc["_id"]},
#         {"$unset": update_fields}
#     )
#
#     # İsteğe bağlı: Description içinden de ürün isimlerini temizlemek istiyorsan burayı ekleyebilirim.
#
# print("✅ Man1 koleksiyonunda Product 21-25 başarıyla silindi!")
