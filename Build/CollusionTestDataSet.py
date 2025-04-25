import pymongo
from datetime import timedelta

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# === Full Tarama Fonksiyonu ===
def full_scan_collusion_test(leader_shop, follower_shops, delay_mapping):
    print(f"\n✨ FULL SCAN Collusion Test: {leader_shop} -> {follower_shops}")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    leader_dates = leader_col.distinct("Date")

    for date in leader_dates:
        leader_doc = leader_col.find_one({"Date": date})
        if not leader_doc:
            continue

        # Her ürün için
        for manu_key in [k for k in leader_doc if k.endswith("Products")]:
            products = leader_doc[manu_key]

            for i in range(1, 100):  # Max 100 ürün
                pname_key = f"Product {i}"
                pprice_key = f"Product {i} Price"

                if pname_key not in products or pprice_key not in products:
                    break

                pname = products[pname_key]
                price = products[pprice_key]

                for follower_shop in follower_shops:
                    follower_col = follower_cols[follower_shop]
                    delay = delay_mapping[follower_shop]
                    delayed_date = date + timedelta(days=delay)

                    follower_doc = follower_col.find_one({"Date": delayed_date})
                    if not follower_doc:
                        continue

                    # Follower mağazada aynı ürün aynı fiyat mı?
                    for fmanu_key in [k for k in follower_doc if k.endswith("Products")]:
                        fproducts = follower_doc[fmanu_key]

                        for j in range(1, 100):
                            fpname_key = f"Product {j}"
                            fpprice_key = f"Product {j} Price"

                            if fpname_key not in fproducts or fpprice_key not in fproducts:
                                break

                            if fproducts[fpname_key] == pname and fproducts[fpprice_key] == price:
                                print(f"\n🔎 Tarih: {date.date()}\n- Product: {pname}\n- Leader: {leader_shop}\n- Followers:\n   ➔ {follower_shop} (Delay: {delay} gün)")

# === Hızlı Tarama Fonksiyonu ===
def fast_scan_collusion_test(leader_shop, follower_shops, delay_mapping):
    print(f"\n🌟 FAST SCAN Collusion Test: {leader_shop} -> {follower_shops}")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    leader_dates = leader_col.distinct("Date")

    for date in leader_dates:
        leader_doc = leader_col.find_one({"Date": date})
        if not leader_doc:
            continue

        for manu_key in [k for k in leader_doc if k.endswith("Products")]:
            products = leader_doc[manu_key]

            for i in range(1, 4):  # Sadece ilk 3 ürünle sınırlı hızlı test
                pname_key = f"Product {i}"
                pprice_key = f"Product {i} Price"

                if pname_key not in products or pprice_key not in products:
                    break

                pname = products[pname_key]
                price = products[pprice_key]

                for follower_shop in follower_shops:
                    follower_col = follower_cols[follower_shop]
                    delay = delay_mapping[follower_shop]
                    delayed_date = date + timedelta(days=delay)

                    follower_doc = follower_col.find_one({"Date": delayed_date})
                    if not follower_doc:
                        continue

                    for fmanu_key in [k for k in follower_doc if k.endswith("Products")]:
                        fproducts = follower_doc[fmanu_key]

                        for j in range(1, 100):
                            fpname_key = f"Product {j}"
                            fpprice_key = f"Product {j} Price"

                            if fpname_key not in fproducts or fpprice_key not in fproducts:
                                break

                            if fproducts[fpname_key] == pname and fproducts[fpprice_key] == price:
                                print(f"\n🔎 Tarih: {date.date()}\n- Product: {pname}\n- Leader: {leader_shop}\n- Followers:\n   ➔ {follower_shop} (Delay: {delay} gün)")


def load_shop_data(shop_name):
    return list(db[shop_name].find({}).sort("Date", 1))

def detect_collusion_on_price_change(leader_shop, follower_shops):
    print(f"\n🌟 PRICE-CHANGE BASED Collusion Test (Flexible Delay): {leader_shop} -> {follower_shops}")

    leader_data = load_shop_data(leader_shop)
    follower_data = {shop: load_shop_data(shop) for shop in follower_shops}

    previous_prices = {}

    for day_idx, day_record in enumerate(leader_data):
        date = day_record["Date"]

        for manu_key in [k for k in day_record.keys() if k.endswith("Products")]:
            products = day_record[manu_key]

            product_keys = [k for k in products if k.startswith("Product ") and "Price" not in k]
            for p_key in product_keys:
                product_name = products[p_key]
                price_key = p_key + " Price"
                price_value = products.get(price_key)

                if not price_value:
                    continue

                current_price = float(price_value.replace(" TL", "").replace(",", ""))

                # İlk gün sadece kaydet
                if product_name not in previous_prices:
                    previous_prices[product_name] = current_price
                    continue

                # Değişim var mı
                if abs(current_price - previous_prices[product_name]) < 0.01:
                    continue

                # Değişim olmuş ➔ Şimdi followers'ı kontrol et
                print(f"\n🔎 Tarih: {date.strftime('%Y-%m-%d')}")
                print(f"- Product: {product_name}")
                print(f"- Leader: {leader_shop}")
                print(f"- Followers:")

                any_follower = False
                for follower in follower_shops:
                    follower_days = follower_data[follower]

                    # Gecikmeli kontrol ➔ 5 gün içinde değişmiş mi
                    for delay in range(1, 6):
                        delayed_date = date + timedelta(days=delay)
                        for f_day in follower_days:
                            if f_day["Date"] == delayed_date:
                                if manu_key in f_day:
                                    f_products = f_day[manu_key]
                                    for fp_key in [k for k in f_products if k.startswith("Product ") and "Price" not in k]:
                                        if f_products[fp_key] == product_name:
                                            f_price_value = f_products.get(fp_key + " Price")
                                            if f_price_value:
                                                f_price = float(f_price_value.replace(" TL", "").replace(",", ""))
                                                if abs(f_price - current_price) < 1.0:
                                                    print(f"   ➔ {follower} (Delay: {delay} gün)")
                                                    any_follower = True
                                                    break
                if not any_follower:
                    print("   ➔ No follower detected.")

                # Update last seen price
                previous_prices[product_name] = current_price


def analyze_collusion_group(leader_shop, follower_shops):
    print(f"\n\U0001F4C8 Collusion Test: {leader_shop} -> {follower_shops}")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    # Tüm leader kayıtlarını sırala
    leader_data = list(leader_col.find({}).sort("Date", 1))

    # Önceki fiyatları tutalım
    previous_prices = {}

    for record in leader_data:
        date = record["Date"]

        # Her manufacturer için tarama
        for manu_key in [k for k in record if k.endswith("Products")]:
            products = record[manu_key]

            for i in range(1, 100):  # Max 100 ürün destekliyor
                pname_key = f"Product {i}"
                pprice_key = f"Product {i} Price"

                if pname_key not in products or pprice_key not in products:
                    break

                pname = products[pname_key]
                pprice = products[pprice_key]

                # Fiyat değişmiş mi?
                if pname not in previous_prices or previous_prices[pname] != pprice:
                    # Fiyat değişimi tespit edildi
                    print(f"\n\U0001F50D Tarih: {date.strftime('%Y-%m-%d')}\n- Product: {pname}\n- Leader: {leader_shop}")
                    previous_prices[pname] = pprice

                    # Şimdi followerlarda bunu arayacağız
                    for follower, f_col in follower_cols.items():
                        for delay in range(1, 8):  # Maks 7 gün içinde takip aranacak
                            delayed_date = date + timedelta(days=delay)
                            follower_doc = f_col.find_one({"Date": delayed_date})

                            if follower_doc:
                                for fmanu_key in [k for k in follower_doc if k.endswith("Products")]:
                                    fproducts = follower_doc[fmanu_key]
                                    for fi in range(1, 100):
                                        fpname_key = f"Product {fi}"
                                        fpprice_key = f"Product {fi} Price"

                                        if fpname_key not in fproducts or fpprice_key not in fproducts:
                                            break

                                        fpname = fproducts[fpname_key]
                                        fpprice = fproducts[fpprice_key]

                                        if fpname == pname and fpprice == pprice:
                                            print(f"   ➔ {follower} takip etti (Delay: {delay} gün)")
                                            break

    print("\n✅ Analiz tamamlandı!")


def collusion_test(leader_shop, follower_shops, delay_mapping):
    print(f"\n📈 Collusion Test Başladı: {leader_shop} ➔ {follower_shops}")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    # Bütün lider kayıtlarını al
    leader_docs = list(leader_col.find().sort("Date", 1))

    previous_prices = {}

    for leader_doc in leader_docs:
        date = leader_doc["Date"]

        # Her manufacturer için
        for manu_key in [k for k in leader_doc.keys() if k.endswith("Products")]:
            manu_products = leader_doc[manu_key]

            for i in range(1, (len(manu_products) // 2) + 1):
                pname_key = f"Product {i}"
                price_key = f"Product {i} Price"

                pname = manu_products.get(pname_key)
                pprice = manu_products.get(price_key)

                if not pname or not pprice:
                    continue

                previous_price = previous_prices.get(pname)

                # Eğer önceki fiyat farklıysa, zam olmuş demektir
                if previous_price and previous_price != pprice:
                    print(f"\n🔍 Tarih: {date.strftime('%Y-%m-%d')}")
                    print(f"- Ürün: {pname}")
                    print(f"- Lider {leader_shop} zam yaptı.")

                    # Şimdi followerlarda bu ürün değişmiş mi bakalım
                    for follower, f_col in follower_cols.items():
                        delay = delay_mapping[follower]
                        follower_date = date + timedelta(days=delay)
                        follower_doc = f_col.find_one({"Date": follower_date})

                        if not follower_doc:
                            print(f"  ➔ {follower} (Delay: {delay} gün) VERİ YOK")
                            continue

                        colluded = False
                        for manu_follower_key in [k for k in follower_doc.keys() if k.endswith("Products")]:
                            manu_follower_products = follower_doc[manu_follower_key]
                            for fi in range(1, (len(manu_follower_products) // 2) + 1):
                                fpname_key = f"Product {fi}"
                                fprice_key = f"Product {fi} Price"

                                fpname = manu_follower_products.get(fpname_key)
                                fpprice = manu_follower_products.get(fprice_key)

                                if fpname == pname and fpprice != previous_price:
                                    colluded = True
                                    break

                            if colluded:
                                break

                        if colluded:
                            print(f"  ✅ {follower} takip etti! (Delay: {delay} gün)")
                        else:
                            print(f"  ⚠️ {follower} takip etmedi.")

                previous_prices[pname] = pprice

    print("\n✅ Collusion Test Tamamlandı.\n")

def full_collusion_test(leader_shop, follower_shops, follower_delays):
    print(f"\n📈 FULL Collusion Test Başladı: {leader_shop} ➔ {follower_shops}\n")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    # Tüm tarihleri sırala
    leader_dates = list(leader_col.find({}, {"Date": 1}).sort("Date", 1))

    for leader_date_doc in leader_dates:
        leader_date = leader_date_doc["Date"]
        leader_record = leader_col.find_one({"Date": leader_date})

        for manu_key in [k for k in leader_record.keys() if k.endswith("Products")]:
            manu_products = leader_record[manu_key]

            product_indices = sorted([
                int(key.split()[1]) for key in manu_products.keys()
                if key.startswith("Product ") and "Price" not in key
            ])

            for idx in product_indices:
                product_name = manu_products[f"Product {idx}"]
                product_price = manu_products[f"Product {idx} Price"]

                # Her follower'ı kontrol et
                for follower, f_col in follower_cols.items():
                    delay = follower_delays[follower]
                    check_date = leader_date + timedelta(days=delay)

                    follower_record = f_col.find_one({"Date": check_date})
                    if not follower_record:
                        print(f"⚠️ {follower} tarihinde veri yok: {check_date.date()}")
                        continue

                    follower_product = None
                    # Üretici bul ve ürün fiyatı al
                    for follower_manu_key in [k for k in follower_record.keys() if k.endswith("Products")]:
                        follower_products = follower_record[follower_manu_key]
                        for fkey, fvalue in follower_products.items():
                            if fkey.startswith("Product ") and "Price" not in fkey and fvalue == product_name:
                                follower_product = follower_products.get(f"Product {fkey.split()[1]} Price")
                                break
                        if follower_product:
                            break

                    # Kontrol
                    if follower_product == product_price:
                        print(f"✅ {leader_date.date()} - Ürün: {product_name} | {follower} doğru şekilde takip etti (Delay: {delay} gün)")
                    else:
                        print(f"⚠️ {leader_date.date()} - Ürün: {product_name} | {follower} TAKİP ETMEDİ veya Fiyat UYUŞMUYOR! (Delay: {delay} gün)")

    print("\n✅ FULL Collusion Test Tamamlandı.")

def full_collusion_test_based_on_leader_price_change(leader_shop, follower_shops, follower_delays):
    print(f"\n📈 PRICE-CHANGE-BASED Collusion Test Başladı: {leader_shop} ➔ {follower_shops}\n")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    leader_dates = list(leader_col.find({}, {"Date": 1}).sort("Date", 1))
    leader_dates = [d["Date"] for d in leader_dates]

    # Önce liderin tüm günlerdeki fiyatlarını al
    previous_prices = {}

    for date in leader_dates:
        leader_doc = leader_col.find_one({"Date": date})

        for manu_key in [k for k in leader_doc.keys() if k.endswith("Products")]:
            manu_products = leader_doc[manu_key]

            product_indices = sorted([
                int(key.split()[1]) for key in manu_products.keys()
                if key.startswith("Product ") and "Price" not in key
            ])

            for idx in product_indices:
                product_name = manu_products[f"Product {idx}"]
                product_price = manu_products[f"Product {idx} Price"]

                # Eğer ürünün eski fiyatı var ve değişmişse zam yapıldı demektir
                if product_name in previous_prices and previous_prices[product_name] != product_price:
                    print(f"🔍 {date.date()} - Ürün: {product_name} için LİDER zam yaptı!")

                    # Şimdi followerlara bakalım
                    for follower, f_col in follower_cols.items():
                        delay = follower_delays[follower]
                        follower_date = date + timedelta(days=delay)

                        follower_doc = f_col.find_one({"Date": follower_date})
                        if not follower_doc:
                            print(f"  ⚠️ {follower} tarihinde veri yok: {follower_date.date()}")
                            continue

                        follower_price = None
                        for f_manu_key in [k for k in follower_doc.keys() if k.endswith("Products")]:
                            follower_products = follower_doc[f_manu_key]
                            for f_idx in range(1, 100):  # Ürün 1-99 arası olabilir
                                if f"Product {f_idx}" in follower_products and follower_products[f"Product {f_idx}"] == product_name:
                                    follower_price = follower_products.get(f"Product {f_idx} Price")
                                    break
                            if follower_price:
                                break

                        if follower_price == product_price:
                            print(f"    ✅ {follower} takip etti! (Delay: {delay} gün)")
                        else:
                            print(f"    ❌ {follower} takip ETMEDİ veya fiyat farklı!")

                # Son fiyatı güncelle
                previous_prices[product_name] = product_price

    print("\n✅ PRICE-CHANGE-BASED Full Test Tamamlandı.")


def advanced_full_collusion_test(leader_shop, follower_shops, follower_delays):
    """
    Lider ve followerların tüm price change günlerini bulur ve delay uyumluluğunu kontrol eder.
    """

    # --- Bağlantılar ---
    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    # --- 1. Lider shop'ın price change günlerini bul ---
    leader_changes = detect_price_changes(leader_col)

    # --- 2. Follower shopların price change günlerini bul ---
    follower_changes = {shop: detect_price_changes(f_col) for shop, f_col in follower_cols.items()}

    # --- 3. Çıktı: Price change günleri ---
    print("\n🔵 Lider Price Change Günleri:")
    for date, product in leader_changes:
        print(f"  📅 {date.date()} - {product}")

    for shop in follower_shops:
        print(f"\n🟡 {shop} Price Change Günleri:")
        for date, product in follower_changes[shop]:
            print(f"  📅 {date.date()} - {product}")

    # --- 4. Follower Delay Kontrolü ---
    print("\n🧠 Delay ve Takip Kontrolü Başlıyor:")

    for leader_date, product_name in leader_changes:
        print(f"\n🔍 {leader_date.date()} - Ürün: {product_name}")

        for follower in follower_shops:
            expected_min = leader_date + timedelta(days=follower_delays[follower] - 1)
            expected_max = leader_date + timedelta(days=follower_delays[follower] + 1)

            found = False
            for f_date, f_product in follower_changes[follower]:
                if f_product == product_name and expected_min <= f_date <= expected_max:
                    print(f"  ✅ {follower} doğru takip etti! (Gözlenen: {f_date.date()}, Beklenen: {expected_min.date()} - {expected_max.date()})")
                    found = True
                    break

            if not found:
                print(f"  ❌ {follower} takip ETMEDİ!")

    print("\n✅ Gelişmiş Full Collusion Testi Tamamlandı.")

def detect_price_changes(collection):
    """
    Verilen shop collection'ı için ürün bazında price change günlerini bulur.
    Dönüş: [(date, product_name), ...]
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

                if pname in previous_prices and previous_prices[pname] != pprice:
                    changes.append((date, pname))

                previous_prices[pname] = pprice

    return changes



# === Kullanım Örnekleri ===
# full_scan_collusion_test("Shop 31", ["Shop 32", "Shop 33"], {"Shop 32": 2, "Shop 33": 1})
# fast_scan_collusion_test("Shop 31", ["Shop 32", "Shop 33"], {"Shop 32": 2, "Shop 33": 1})
# detect_collusion_on_price_change("Shop 31", ["Shop 32", "Shop 33"])
# analyze_collusion_group("Shop 31", ["Shop 32", "Shop 33"])

# delay_mapping = {
#     "Shop 32": 3,  # 3 gün gecikmeyle takip ediyor
#     "Shop 33": 6   # 6 gün gecikmeyle takip ediyor
# }
#
# collusion_test("Shop 31", ["Shop 32", "Shop 33"], delay_mapping)

# full_collusion_test_based_on_leader_price_change(
#     leader_shop="Shop 31",
#     follower_shops=["Shop 32", "Shop 33"],
#     follower_delays={
#         "Shop 32": 3,
#         "Shop 33": 6
#     }
# )

# # # Kullanım:
# leader_shop = "Shop 31"
# follower_shops = ["Shop 32", "Shop 33"]
# follower_delays = {
#     "Shop 32": 4,   # 3 gün delay
#     "Shop 33": 3    # 6 gün delay
# }
#
# # Fonksiyonu çağır:
# advanced_full_collusion_test(leader_shop, follower_shops, follower_delays)


# Kullanım:
leader_shop = "Shop 34"
follower_shops = ["Shop 35", "Shop 36", "Shop 37"]
follower_delays = {
    "Shop 35": 2,   # 3 gün delay
    "Shop 36": 7,   # 5 gün delay
    "Shop 37": 1    # 6 gün delay
}

# Fonksiyonu çağır:
advanced_full_collusion_test(leader_shop, follower_shops, follower_delays)