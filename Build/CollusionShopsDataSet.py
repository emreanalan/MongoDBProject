# import pymongo
# import random
# from datetime import datetime, timedelta
# from copy import deepcopy
#
# # === MongoDB Bağlantısı === #
# client = pymongo.MongoClient(
#     "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
#     serverSelectionTimeoutMS=300000,  # 5 dakika
#     socketTimeoutMS=600000,            # 10 dakika
#     connectTimeoutMS=300000
# )
# db = client["DataSet"]
#
# # === Tüm Ürün-Cost Verisini RAM'e Cache'le === #
# print("🔵 Products cache oluşturuluyor...")
# products_cursor = db["Products"].find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
# products_cache = {(p["Product Name"], p["Date"]): p["Cost"] for p in products_cursor}
# print(f"✅ {len(products_cache)} ürün kaydı cache'lendi.\n")
#
# # === Tüm Manufacturer Verilerini RAM'e Cache'le === #
# print("🔵 Manufacturer cache oluşturuluyor...")
# manufacturers = [f"Man{i}" for i in range(1, 26)]
# manufacturer_cache = {}
#
# for manu in manufacturers:
#     manu_cursor = db[manu].find({}, {"Date": 1, **{f"Product {i}": 1 for i in range(1, 21)}, **{f"Product {i} Price": 1 for i in range(1, 21)}})
#     manufacturer_cache[manu] = {doc["Date"]: doc for doc in manu_cursor}
#
# print(f"✅ {len(manufacturer_cache)} manufacturer cache'lendi.\n")
#
# # === Tarihler ve Zam Günleri Ayarları === #
# start_date = datetime(2025, 1, 1)
# total_days = 115
# dates = [start_date + timedelta(days=i) for i in range(total_days)]
#
# def select_zam_days():
#     zam_days = []
#     possible_days = list(range(7, len(dates)))
#
#     while True:
#         if len(zam_days) >= 6 or not possible_days:
#             break
#         day = random.choice(possible_days)
#         if all(abs(day - other) >= 8 for other in zam_days):
#             zam_days.append(day)
#             possible_days = [d for d in possible_days if abs(d - day) >= 8]
#         if len(zam_days) == 3 and random.random() > 0.8:
#             break
#         if len(zam_days) == 4 and random.random() > 0.6:
#             break
#         if len(zam_days) == 5 and random.random() > 0.4:
#             break
#     return sorted(zam_days)
#
# def create_collusion_groups_from_list(shop_ids):
#     random.shuffle(shop_ids)
#     groups = []
#     idx = 0
#     while idx < len(shop_ids):
#         group_size = random.choice([3, 4, 5])
#         group = [f"Shop {i}" for i in shop_ids[idx:idx+group_size]]
#         if len(group) >= 3:
#             groups.append(group)
#             idx += group_size
#         else:
#             if groups:
#                 groups[-1].extend([f"Shop {i}" for i in shop_ids[idx:]])
#             break
#     return groups
#
# def generate_collusion_data(collusion_groups):
#     print("🚀 Collusion ShopsDataSet oluşturuluyor...\n")
#
#     for group_num, group_shops in enumerate(collusion_groups, start=1):
#         leader_shop = group_shops[0]
#         follower_shops = group_shops[1:]
#
#         zam_days = select_zam_days()
#         zam_real_dates = [dates[d] for d in zam_days]
#
#         follower_delays = {shop: random.randint(1, 7) for shop in follower_shops}
#         selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))
#
#         product_profits = {}
#
#         print(f"🔵 Grup {group_num}:")
#         print(f"⭐ Lider: {leader_shop}")
#         print(f"🛒 Followerlar: {follower_shops}")
#         print(f"📅 Zam Günleri: {[d.strftime('%Y-%m-%d') for d in zam_real_dates]}")
#         print(f"⚙️ Gecikmeler: {follower_delays}\n")
#
#         leader_bulk_ops = []
#         previous_prices = {}
#
#         for day_idx, current_date in enumerate(dates):
#             doc = {
#                 "Date": current_date,
#                 "Store Type": leader_shop,
#                 "Description": f"Product prices for {leader_shop} on {current_date.strftime('%Y-%m-%d')}"
#             }
#             for manu in selected_manufacturers:
#                 manu_data = manufacturer_cache.get(manu, {}).get(current_date)
#                 if not manu_data:
#                     continue
#
#                 manu_doc = {}
#                 product_keys = sorted([k for k in manu_data.keys() if k.startswith("Product ") and "Price" not in k], key=lambda x: int(x.split()[1]))
#
#                 for i, prod_key in enumerate(product_keys):
#                     pname = manu_data[prod_key]
#                     cost_str = products_cache.get((pname, current_date))
#                     if not cost_str:
#                         continue
#
#                     manufacturer_price = float(cost_str.replace(",", "").replace(" TL", ""))
#
#                     if pname not in product_profits:
#                         product_profits[pname] = random.randint(4, 15)
#
#                     profit_pct = product_profits[pname] / 100
#
#                     if day_idx == 0:
#                         price = manufacturer_price * (1 + profit_pct)
#                         previous_prices[pname] = price
#                     elif day_idx in zam_days:
#                         price = manufacturer_price * (1 + profit_pct)
#                         previous_prices[pname] = price
#                     else:
#                         price = previous_prices[pname]
#
#                     manu_doc[f"Product {i+1}"] = pname
#                     manu_doc[f"Product {i+1} Price"] = f"{price:,.2f} TL"
#
#                 if manu_doc:
#                     doc[f"{manu} Products"] = manu_doc
#
#             leader_bulk_ops.append(pymongo.UpdateOne({"Date": current_date}, {"$set": doc}, upsert=True))
#
#         db[leader_shop].bulk_write(leader_bulk_ops)
#
#         for follower_shop in follower_shops:
#             delay = follower_delays[follower_shop]
#             follower_bulk_ops = []
#             follower_prev_prices = {}
#
#             for day_idx, current_date in enumerate(dates):
#                 delayed_idx = max(0, day_idx - delay)
#                 delayed_date = dates[delayed_idx]
#
#                 doc = {
#                     "Date": current_date,
#                     "Store Type": follower_shop,
#                     "Description": f"Product prices for {follower_shop} on {current_date.strftime('%Y-%m-%d')}"
#                 }
#
#                 for manu in selected_manufacturers:
#                     manu_data = manufacturer_cache.get(manu, {}).get(delayed_date)
#                     if not manu_data:
#                         continue
#
#                     manu_doc = {}
#                     product_keys = sorted([k for k in manu_data.keys() if k.startswith("Product ") and "Price" not in k], key=lambda x: int(x.split()[1]))
#
#                     for i, prod_key in enumerate(product_keys):
#                         pname = manu_data[prod_key]
#                         cost_str = products_cache.get((pname, delayed_date))
#                         if not cost_str:
#                             continue
#
#                         manufacturer_price = float(cost_str.replace(",", "").replace(" TL", ""))
#
#                         profit_pct = product_profits[pname] / 100
#
#                         if delayed_idx == 0:
#                             price = manufacturer_price * (1 + profit_pct)
#                             follower_prev_prices[pname] = price
#                         elif delayed_idx in zam_days:
#                             price = manufacturer_price * (1 + profit_pct)
#                             follower_prev_prices[pname] = price
#                         else:
#                             price = follower_prev_prices[pname]
#
#                         manu_doc[f"Product {i+1}"] = pname
#                         manu_doc[f"Product {i+1} Price"] = f"{price:,.2f} TL"
#
#                     if manu_doc:
#                         doc[f"{manu} Products"] = manu_doc
#
#                 follower_bulk_ops.append(pymongo.UpdateOne({"Date": current_date}, {"$set": doc}, upsert=True))
#
#             batch_size = 30
#             for i in range(0, len(follower_bulk_ops), batch_size):
#                 batch = follower_bulk_ops[i:i + batch_size]
#                 db[follower_shop].bulk_write(batch)
#
#     print("\n✅ Tüm Collusion Shops başarıyla ultra hızlı oluşturuldu!")
#
#
import pymongo
import random
from datetime import datetime, timedelta
from collections import defaultdict

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,
    socketTimeoutMS=600000,
    connectTimeoutMS=300000
)
db = client["DataSet"]

manufacturers = [f"Man {i}" for i in range(1, 26)]

print("🔵 Manufacturer cache oluşturuluyor...")
manufacturer_cache = {}
for manu in manufacturers:
    cursor = db[manu].find({}, {"_id": 0})
    manufacturer_cache[manu] = {doc["Date"]: doc for doc in cursor}
print("✅ Manufacturer cache tamamlandı.\n")

def create_collusion_groups_from_list(shop_ids):
    shop_ids = list(shop_ids)
    random.shuffle(shop_ids)
    groups = []
    idx = 0
    while idx < len(shop_ids):
        group_size = random.choice([3, 4, 5])
        group = [f"Shop {i}" for i in shop_ids[idx:idx+group_size]]
        if len(group) >= 3:
            groups.append(group)
            idx += group_size
        else:
            if groups:
                groups[-1].extend([f"Shop {i}" for i in shop_ids[idx:]])
            break
    return groups

def assign_manufacturers_to_groups(collusion_groups):
    group_manus_map = {}
    for group_num, group_shops in enumerate(collusion_groups, start=1):
        common_manus = random.sample(manufacturers, 2)
        remaining_manus = [m for m in manufacturers if m not in common_manus]
        shop_manus = {}
        print(f"\n🔹 Grup {group_num}")
        print(f"🔁 Ortak Manufacturer'lar: {common_manus}")
        for shop in group_shops:
            extra_manus = random.sample(remaining_manus, random.choice([1, 2]))
            full_manus = common_manus + extra_manus
            shop_manus[shop] = full_manus
            print(f"  🛍️ {shop} -> {full_manus}")
        group_manus_map[group_num] = {
            "group_shops": group_shops,
            "common_manus": common_manus,
            "shop_manus": shop_manus
        }
    return group_manus_map

def select_zam_days(dates):
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
    return [dates[i] for i in sorted(zam_days)]

def generate_collusion_shops(group_manus_map):
    print("\n🧠 Ortak ürünler belirleniyor ve collusion ürünleri seçiliyor...\n")
    all_dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(115)]

    for group_num, group_data in group_manus_map.items():
        common_manus = group_data["common_manus"]
        group_shops = group_data["group_shops"]
        shop_manus_map = group_data["shop_manus"]

        leader = group_shops[0]
        followers = group_shops[1:]
        delays = {shop: (0 if shop == leader else random.randint(1, 7)) for shop in group_shops}
        zam_days = select_zam_days(all_dates)

        sample_date = all_dates[0]
        all_products = set()
        for manu in common_manus:
            manu_doc = manufacturer_cache[manu].get(sample_date)
            if not manu_doc:
                continue
            for i in range(1, 21):
                pname = manu_doc.get(f"Product {i}")
                if pname:
                    all_products.add(pname)

        all_products = list(all_products)
        collusion_products = random.sample(all_products, max(1, int(len(all_products) * random.uniform(0.15, 0.30))))
        collusion_price_map = {p: round(random.uniform(5.0, 10.0), 2) / 100 for p in collusion_products}

        print(f"\n🔵 Grup {group_num} - Ortak Tarih: {sample_date.strftime('%Y-%m-%d')}")
        print(f"   ⭐ Lider Shop: {leader}")
        print(f"   🛒 Followerlar: {followers}")
        print(f"   ⏱️ Delay Günleri: {delays}")
        print(f"   📅 Zam Günleri: {[d.strftime('%Y-%m-%d') for d in zam_days]}")
        print(f"   🎯 Collusion Ürünleri: {collusion_products}\n")

        for shop in group_shops:
            shop_collection = db[shop]
            profit_variation = defaultdict(lambda: round(random.uniform(-0.1, 0.1), 3))
            previous_prices = {}
            bulk_ops = []

            for date in all_dates:
                doc = {
                    "Date": date,
                    "Store Type": shop,
                    "Description": f"Generated collusion prices on {date.strftime('%Y-%m-%d')}"
                }
                shop_manus = shop_manus_map[shop]

                for manu in shop_manus:
                    manu_doc = {}
                    for i in range(1, 21):
                        pname = None
                        base_price = None
                        for zam_day in zam_days:
                            write_day = zam_day + timedelta(days=delays[shop])
                            if date == write_day:
                                base_doc = manufacturer_cache[manu].get(zam_day)
                                if base_doc:
                                    pname = base_doc.get(f"Product {i}")
                                    base_str = base_doc.get(f"Product {i} Price")
                                    if pname and base_str:
                                        base_price = float(base_str.replace(",", "").replace(" TL", ""))
                                        profit_pct = collusion_price_map.get(pname, 0) * 100
                                        final_price = base_price * (1 + profit_pct / 100)
                                        break

                        if pname is None:
                            manu_data = manufacturer_cache[manu].get(date)
                            if manu_data:
                                pname = manu_data.get(f"Product {i}")
                                base_str = manu_data.get(f"Product {i} Price")
                                if pname and base_str:
                                    base_price = float(base_str.replace(",", "").replace(" TL", ""))
                                    if date in zam_days:
                                        profit_pct = round(random.uniform(2.0, 12.0) + profit_variation[pname] * 100, 2)
                                        final_price = base_price * (1 + profit_pct / 100)
                                        previous_prices[pname] = final_price
                                    else:
                                        profit_pct = None
                                        final_price = previous_prices.get(pname, base_price)
                        if pname and base_price:
                            manu_doc[f"Product {i}"] = pname
                            manu_doc[f"Product {i} Manufacturer Price"] = f"{base_price:,.2f} TL"
                            if profit_pct is not None:
                                manu_doc[f"Product {i} Shop Profit %"] = profit_pct
                            manu_doc[f"Product {i} Price"] = f"{final_price:,.2f} TL"
                    if manu_doc:
                        doc[f"{manu} Products"] = manu_doc
                bulk_ops.append(pymongo.UpdateOne({"Date": date}, {"$set": doc}, upsert=True))
            if bulk_ops:
                shop_collection.bulk_write(bulk_ops)

if __name__ == "__main__":
    collusion_groups = create_collusion_groups_from_list(range(1, 21))
    group_structure = assign_manufacturers_to_groups(collusion_groups)
    generate_collusion_shops(group_structure)
