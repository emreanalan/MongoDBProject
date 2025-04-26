# --- DOSYA BAŞI --- #
import pymongo
from datetime import datetime

# 📡 MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,  # 5 dakika
    socketTimeoutMS=600000,  # 10 dakika
    connectTimeoutMS=300000  # 5 dakika
)
db = client["DataSet"]


# --- FONKSİYONLAR --- #

def extract_product_movements(shop_list):
    product_movements = {}

    for shop in shop_list:
        print(f"🔍 Shop taranıyor: {shop}")
        collection = db[shop]
        product_movements[shop] = {}

        all_records = list(collection.find({}).sort("Date", 1))

        previous_prices = {}

        for record in all_records:
            date = record["Date"]

            for key, value in record.items():
                if "Product" in key and "Price" not in key:
                    product_name = value
                    price_key = key + " Price"
                    price_value = record.get(price_key)

                    if price_value is None:
                        continue

                    price_float = float(price_value.replace(" TL", "").replace(",", ""))

                    if product_name not in previous_prices:
                        previous_prices[product_name] = price_float
                        continue

                    old_price = previous_prices[product_name]
                    if old_price > 0 and abs(price_float - old_price) / old_price > 0.0199:
                        if product_name not in product_movements[shop]:
                            product_movements[shop][product_name] = []
                        product_movements[shop][product_name].append(date)

                        previous_prices[product_name] = price_float
                    else:
                        previous_prices[product_name] = price_float

    return product_movements


def scan_all_shops(shop_list):
    """
    Tüm verilen shopları tarayıp ürün bazlı fiyat değişimlerini listeler.
    """
    for shop_name in shop_list:
        print(f"\n🔎 Shop inceleniyor: {shop_name}")
        collection = db[shop_name]
        changes = detect_price_changes(collection)

        if not changes:
            print("  ⚪ Hiç fiyat değişimi bulunamadı.")
        else:
            product_changes = {}
            for date, pname in changes:
                if pname not in product_changes:
                    product_changes[pname] = []
                product_changes[pname].append(date)

            for pname, dates in product_changes.items():
                print(f"  🛒 {pname}: {len(dates)} değişim ➔ {', '.join(d.strftime('%Y-%m-%d') for d in dates)}")


def detect_price_changes(collection):
    """
    Verilen shop collection'ı için ürün bazında price change günlerini bulur.
    Yüzdesel olarak %1.99'dan fazla değişim varsa değişim olarak kabul edilir.
    """
    previous_prices = {}
    changes = []

    dates = list(collection.find({}, {"Date": 1}).sort("Date", 1))
    dates = [d["Date"] for d in dates]

    for date in dates:
        doc = collection.find_one({"Date": date})
        if not doc:
            continue

        for manu_key in [k for k in doc.keys() if k.endswith("Products")]:
            manu_products = doc[manu_key]

            product_indices = sorted([
                int(k.split()[1]) for k in manu_products.keys()
                if k.startswith("Product ") and "Price" not in k
            ])

            for idx in product_indices:
                pname = manu_products.get(f"Product {idx}")
                pprice = manu_products.get(f"Product {idx} Price")

                if pname is None or pprice is None:
                    continue

                current_price = float(pprice.replace(" TL", "").replace(",", ""))

                if pname in previous_prices:
                    old_price = previous_prices[pname]
                    if old_price > 0 and abs(current_price - old_price) / old_price > 0.0199:
                        changes.append((date, pname))

                previous_prices[pname] = current_price

    return changes


# --- ANA AKIŞ --- #

if __name__ == "__main__":
    print("🏁 Ürün fiyat değişim hareketleri çıkarılıyor...\n")

    normal_shops = [f"Shop {i}" for i in range(1, 91)]
    collusion_shops_batch1 = [f"Shop {i}" for i in range(91, 121)]
    collusion_shops_batch2 = [f"Shop {i}" for i in range(121, 161)]

    normal_movements = extract_product_movements(normal_shops)

    print("\n🔵 İlk Collusion Batch (Shop 91–120) işleniyor...\n")
    collusion_movements_batch1 = extract_product_movements(collusion_shops_batch1)

    print("\n🟡 İkinci Collusion Batch (Shop 121–160) işleniyor...\n")
    collusion_movements_batch2 = extract_product_movements(collusion_shops_batch2)

    print("\n✅ Tüm ürün fiyat hareketleri başarıyla çıkarıldı!")

    # --- TEST BÖLÜMÜ --- #

    print("\n📋 TEST: İlk 3 normal shop ve 3 collusion shop ürün hareketleri gösteriliyor...\n")

    # Normal Shops
    for shop in list(normal_movements.keys())[:3]:
        print(f"🟦 Normal Shop: {shop}")
        products = list(normal_movements[shop].items())
        if not products:
            print("  ⚪ Hiç ürün fiyat değişimi yok.")
        else:
            for product, dates in products[:3]:
                print(f"  - {product}: {len(dates)} değişim ➔ {', '.join(d.strftime('%Y-%m-%d') for d in dates)}")

    # Collusion Shops (Batch 1)
    collusion_keys_batch1 = list(collusion_movements_batch1.keys())

    print("\n🟥 İlk Batch (Shop 91–120) Collusion Shops")
    for shop in collusion_keys_batch1[:3]:
        print(f"🟥 Collusion Shop (Batch 1): {shop}")
        products = list(collusion_movements_batch1[shop].items())
        if not products:
            print("  ⚪ Hiç ürün fiyat değişimi yok.")
        else:
            for product, dates in products[:3]:
                print(f"  - {product}: {len(dates)} değişim ➔ {', '.join(d.strftime('%Y-%m-%d') for d in dates)}")

    # Collusion Shops (Batch 2)
    collusion_keys_batch2 = list(collusion_movements_batch2.keys())

    if collusion_keys_batch2:
        print("\n🟨 İkinci Batch (Shop 121–160) Collusion Shops")
        for shop in collusion_keys_batch2[:3]:
            print(f"🟨 Collusion Shop (Batch 2): {shop}")
            products = list(collusion_movements_batch2[shop].items())
            if not products:
                print("  ⚪ Hiç ürün fiyat değişimi yok.")
            else:
                for product, dates in products[:3]:
                    print(f"  - {product}: {len(dates)} değişim ➔ {', '.join(d.strftime('%Y-%m-%d') for d in dates)}")
    else:
        print("\n⚠️ İkinci batch collusion shop bulunamadı.")

    # --- YENİ TÜM DATASET TARAMASI --- #
    print("\n🌐 Şimdi tüm shoplarda full ürün değişim taraması başlıyor...")
    scan_all_shops(normal_shops + collusion_shops_batch1 + collusion_shops_batch2)
