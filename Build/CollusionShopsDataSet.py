#İlk Deneme
# import pymongo
# import random
# from datetime import datetime, timedelta
# from copy import deepcopy
#
# # MongoDB connection
# client = pymongo.MongoClient(
#     "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# )
# db = client["DataSet"]
#
# products_collection = db["Products"]
# manufacturers = [f"Man{i}" for i in range(1, 26)]
#
# # Product cache (hız için)
# product_cursor = products_collection.find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
# product_cache = {(p["Product Name"], p["Date"]): p["Cost"] for p in product_cursor}
#
# # 115 gün tarih listesi
# start_date = datetime(2025, 1, 1)
# dates = [start_date + timedelta(days=i) for i in range(115)]
#
#
# def select_zam_days():
#     zam_days = []
#     possible_days = list(range(7, len(dates)))  # İlk 7 günü atlıyoruz
#
#     while True:
#         if len(zam_days) >= 6:
#             break
#         if not possible_days:
#             break
#
#         day = random.choice(possible_days)
#         if all(abs(day - other) >= 8 for other in zam_days):
#             zam_days.append(day)
#             possible_days = [d for d in possible_days if abs(d - day) >= 8]
#
#         if len(zam_days) == 3 and random.random() > 0.8:
#             break
#         if len(zam_days) == 4 and random.random() > 0.6:
#             break
#         if len(zam_days) == 5 and random.random() > 0.4:
#             break
#
#     zam_days = sorted(zam_days)
#     return zam_days
#
#
# def create_collusion_group(leader_shop, follower_shops):
#     selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))
#     print(f"\n{leader_shop} collusion grubu --> {selected_manufacturers}")
#
#     leader_col = db[leader_shop]
#     follower_cols = {shop: db[shop] for shop in follower_shops}
#
#     follower_delays = {shop: random.randint(1, 7) for shop in follower_shops}
#     print(f"Delayler: {follower_delays}")
#
#     zam_days = select_zam_days()
#     print(f"Zam Günleri: {[dates[d].strftime('%Y-%m-%d') for d in zam_days]}")
#
#     leader_prices = {}
#     previous_docs = {follower: None for follower in follower_shops}
#
#     for day_idx, current_date in enumerate(dates):
#         doc = {
#             "Date": current_date,
#             "Store Type": leader_shop,
#             "Description": f"Prices for {leader_shop} on {current_date.strftime('%Y-%m-%d')}"
#         }
#
#         for manu in selected_manufacturers:
#             manu_doc = {}
#             manu_data = db[manu].find_one({"Date": current_date})
#             if not manu_data:
#                 continue
#
#             product_keys = sorted(
#                 [k for k in manu_data if k.startswith("Product ") and "Price" not in k],
#                 key=lambda k: int(k.split()[1])
#             )
#
#             for i, key in enumerate(product_keys):
#                 pname = manu_data[key]
#                 base_cost_str = product_cache.get((pname, current_date))
#                 if not base_cost_str:
#                     continue
#
#                 base = float(base_cost_str.replace(" TL", "").replace(",", ""))
#
#                 if day_idx in zam_days and random.random() < random.uniform(0.2, 0.5):
#                     profit = random.randint(2, 12)
#                     final = base * (1 + profit / 100)
#                 else:
#                     final = leader_prices.get(pname, base)
#
#                 leader_prices[pname] = final
#
#                 manu_doc[f"Product {i + 1}"] = pname
#                 manu_doc[f"Product {i + 1} Price"] = f"{final:,.2f} TL"
#
#             if manu_doc:
#                 doc[f"{manu} Products"] = manu_doc
#
#         leader_col.update_one({"Date": current_date}, {"$set": doc}, upsert=True)
#
#         # Followers
#         for follower, f_col in follower_cols.items():
#             delay = follower_delays[follower]
#             delayed_date = current_date + timedelta(days=delay)
#
#             if delayed_date > dates[-1]:
#                 continue
#
#             if previous_docs[follower] is None:
#                 # İlk veri
#                 follower_doc = deepcopy(doc)
#                 follower_doc["Date"] = delayed_date
#                 follower_doc["Store Type"] = follower
#                 follower_doc[
#                     "Description"] = f"[Following {leader_shop}] Prices for {follower} on {delayed_date.strftime('%Y-%m-%d')}"
#                 f_col.update_one({"Date": delayed_date}, {"$set": follower_doc}, upsert=True)
#                 previous_docs[follower] = follower_doc
#             else:
#                 # Aradaki günler için aynı veriyi taşı
#                 last_date = previous_docs[follower]["Date"]
#                 while last_date < delayed_date:
#                     carry_doc = deepcopy(previous_docs[follower])
#                     carry_doc["Date"] = last_date + timedelta(days=1)
#                     f_col.update_one({"Date": carry_doc["Date"]}, {"$set": carry_doc}, upsert=True)
#                     last_date = carry_doc["Date"]
#
#                 follower_doc = deepcopy(doc)
#                 follower_doc["Date"] = delayed_date
#                 follower_doc["Store Type"] = follower
#                 follower_doc[
#                     "Description"] = f"[Following {leader_shop}] Prices for {follower} on {delayed_date.strftime('%Y-%m-%d')}"
#                 f_col.update_one({"Date": delayed_date}, {"$set": follower_doc}, upsert=True)
#                 previous_docs[follower] = follower_doc
#
#     print(f"✅ {leader_shop} grubu tamamlandı.")
#
#
# def generate_collusion_groups(start_shop=91, end_shop=160, n_groups=70):
#     available_shops = list(range(start_shop, end_shop + 1))
#     random.shuffle(available_shops)
#
#     for _ in range(n_groups):
#         if len(available_shops) < 3:
#             break
#
#         group_size = random.choice([3, 4, 5])
#         if len(available_shops) < group_size:
#             group_size = len(available_shops)
#
#         group_shops = available_shops[:group_size]
#         available_shops = available_shops[group_size:]
#
#         leader = f"Shop {group_shops[0]}"
#         followers = [f"Shop {shop}" for shop in group_shops[1:]]
#
#         print(f"🚀 Collusion Grubu: {leader} ➔ {followers}")
#         create_collusion_group(leader, followers)
#
#
# generate_collusion_groups()
import pymongo
import random
from datetime import datetime, timedelta
from copy import deepcopy

# === MongoDB Bağlantısı === #
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,  # 5 dakika
    socketTimeoutMS=600000,            # 10 dakika
    connectTimeoutMS=300000
)
db = client["DataSet"]

# === Tüm Ürün-Cost Verisini RAM'e Cache'le === #
print("🔵 Products cache oluşturuluyor...")
products_cursor = db["Products"].find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
products_cache = {(p["Product Name"], p["Date"]): p["Cost"] for p in products_cursor}
print(f"✅ {len(products_cache)} ürün kaydı cache'lendi.\n")

# === Tüm Manufacturer Verilerini RAM'e Cache'le === #
print("🔵 Manufacturer cache oluşturuluyor...")
manufacturers = [f"Man{i}" for i in range(1, 26)]
manufacturer_cache = {}

for manu in manufacturers:
    manu_cursor = db[manu].find({}, {"Date": 1, **{f"Product {i}": 1 for i in range(1, 21)}, **{f"Product {i} Price": 1 for i in range(1, 21)}})
    manufacturer_cache[manu] = {doc["Date"]: doc for doc in manu_cursor}

print(f"✅ {len(manufacturer_cache)} manufacturer cache'lendi.\n")

# === Tarihler ve Zam Günleri Ayarları === #
start_date = datetime(2025, 1, 1)
total_days = 115
dates = [start_date + timedelta(days=i) for i in range(total_days)]

def select_zam_days():
    zam_days = []
    possible_days = list(range(7, len(dates)))

    while True:
        if len(zam_days) >= 6 or not possible_days:
            break
        day = random.choice(possible_days)
        if all(abs(day - other) >= 8 for other in zam_days):
            zam_days.append(day)
            possible_days = [d for d in possible_days if abs(d - day) >= 8]
        if len(zam_days) == 3 and random.random() > 0.8:
            break
        if len(zam_days) == 4 and random.random() > 0.6:
            break
        if len(zam_days) == 5 and random.random() > 0.4:
            break
    return sorted(zam_days)

def create_collusion_groups(shop_start, shop_end):
    shops = [f"Shop {i}" for i in range(shop_start, shop_end + 1)]
    random.shuffle(shops)
    groups = []
    idx = 0
    while idx < len(shops):
        group_size = random.choice([3, 4, 5])
        group = shops[idx:idx+group_size]
        if len(group) >= 3:
            groups.append(group)
            idx += group_size
        else:
            groups[-1].extend(group)
            break
    return groups

# === COLLUSION GROUPS OLUŞTUR === #
#collusion_groups = create_collusion_groups(171, 340)
collusion_groups = create_collusion_groups(371, 400)

# === Collusion Shop Verileri Üret === #
print("🚀 Collusion ShopsDataSet oluşturuluyor...\n")

for group_num, group_shops in enumerate(collusion_groups, start=1):
    leader_shop = group_shops[0]
    follower_shops = group_shops[1:]

    zam_days = select_zam_days()
    zam_real_dates = [dates[d] for d in zam_days]

    follower_delays = {shop: random.randint(1, 7) for shop in follower_shops}
    selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))

    # Her ürün için profit seçimi
    product_profits = {}

    print(f"🔵 Grup {group_num}:")
    print(f"⭐ Lider: {leader_shop}")
    print(f"🛒 Followerlar: {follower_shops}")
    print(f"📅 Zam Günleri: {[d.strftime('%Y-%m-%d') for d in zam_real_dates]}")
    print(f"⚙️ Gecikmeler: {follower_delays}\n")

    # --- LİDER İÇİN BELGELERİ HAZIRLA --- #
    leader_bulk_ops = []
    previous_prices = {}

    for day_idx, current_date in enumerate(dates):
        doc = {
            "Date": current_date,
            "Store Type": leader_shop,
            "Description": f"Product prices for {leader_shop} on {current_date.strftime('%Y-%m-%d')}"
        }
        for manu in selected_manufacturers:
            manu_data = manufacturer_cache.get(manu, {}).get(current_date)
            if not manu_data:
                continue

            manu_doc = {}
            product_keys = sorted([k for k in manu_data.keys() if k.startswith("Product ") and "Price" not in k], key=lambda x: int(x.split()[1]))

            for i, prod_key in enumerate(product_keys):
                pname = manu_data[prod_key]
                cost_str = products_cache.get((pname, current_date))
                if not cost_str:
                    continue

                manufacturer_price = float(cost_str.replace(",", "").replace(" TL", ""))

                if pname not in product_profits:
                    product_profits[pname] = random.randint(4, 15)

                profit_pct = product_profits[pname] / 100

                if day_idx == 0:
                    price = manufacturer_price * (1 + profit_pct)
                    previous_prices[pname] = price
                elif day_idx in zam_days:
                    price = manufacturer_price * (1 + profit_pct)
                    previous_prices[pname] = price
                else:
                    price = previous_prices[pname]

                manu_doc[f"Product {i+1}"] = pname
                manu_doc[f"Product {i+1} Price"] = f"{price:,.2f} TL"

            if manu_doc:
                doc[f"{manu} Products"] = manu_doc

        leader_bulk_ops.append(pymongo.UpdateOne({"Date": current_date}, {"$set": doc}, upsert=True))

    db[leader_shop].bulk_write(leader_bulk_ops)

    # --- FOLLOWERLAR İÇİN BELGELERİ HAZIRLA --- #
    for follower_shop in follower_shops:
        delay = follower_delays[follower_shop]
        follower_bulk_ops = []
        follower_prev_prices = {}

        for day_idx, current_date in enumerate(dates):
            delayed_idx = max(0, day_idx - delay)
            delayed_date = dates[delayed_idx]

            doc = {
                "Date": current_date,
                "Store Type": follower_shop,
                "Description": f"Product prices for {follower_shop} on {current_date.strftime('%Y-%m-%d')}"
            }

            for manu in selected_manufacturers:
                manu_data = manufacturer_cache.get(manu, {}).get(delayed_date)
                if not manu_data:
                    continue

                manu_doc = {}
                product_keys = sorted([k for k in manu_data.keys() if k.startswith("Product ") and "Price" not in k], key=lambda x: int(x.split()[1]))

                for i, prod_key in enumerate(product_keys):
                    pname = manu_data[prod_key]
                    cost_str = products_cache.get((pname, delayed_date))
                    if not cost_str:
                        continue

                    manufacturer_price = float(cost_str.replace(",", "").replace(" TL", ""))

                    profit_pct = product_profits[pname] / 100

                    if delayed_idx == 0:
                        price = manufacturer_price * (1 + profit_pct)
                        follower_prev_prices[pname] = price
                    elif delayed_idx in zam_days:
                        price = manufacturer_price * (1 + profit_pct)
                        follower_prev_prices[pname] = price
                    else:
                        price = follower_prev_prices[pname]

                    manu_doc[f"Product {i+1}"] = pname
                    manu_doc[f"Product {i+1} Price"] = f"{price:,.2f} TL"

                if manu_doc:
                    doc[f"{manu} Products"] = manu_doc

            follower_bulk_ops.append(pymongo.UpdateOne({"Date": current_date}, {"$set": doc}, upsert=True))

        # === Bulk Write işlemini küçük parçalara ayır ===
        batch_size = 30  # Maksimum 30 işlem bir seferde
        for i in range(0, len(follower_bulk_ops), batch_size):
            batch = follower_bulk_ops[i:i + batch_size]
            db[follower_shop].bulk_write(batch)

print("\n✅ Tüm Collusion Shops başarıyla ultra hızlı oluşturuldu!")


