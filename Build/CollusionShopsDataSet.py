import pymongo
import random
from datetime import datetime, timedelta
from collections import defaultdict  # Burada defaultdict import ediliyor

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    serverSelectionTimeoutMS=300000,
    socketTimeoutMS=600000,
    connectTimeoutMS=300000
)
db = client["DataSet"]

manufacturers = [f"Man {i}" for i in range(1, 26)]

# Manufacturer Cache
print("🔵 Manufacturer cache oluşturuluyor...")
manufacturer_cache = {}
for manu in manufacturers:
    cursor = db[manu].find({}, {"_id": 0})
    manufacturer_cache[manu] = {doc["Date"]: doc for doc in cursor}
print("✅ Manufacturer cache tamamlandı.\n")


# Collusion Grubu Oluşturma
def create_collusion_groups_from_list(shop_ids):
    random.shuffle(shop_ids)
    groups = []
    idx = 0
    while idx < len(shop_ids):
        group_size = random.choice([3, 4, 5])
        group = [f"Shop {i}" for i in shop_ids[idx:idx + group_size]]
        if len(group) >= 3:
            groups.append(group)
            idx += group_size
        else:
            if groups:
                groups[-1].extend([f"Shop {i}" for i in shop_ids[idx:]])
            break
    return groups


# Manufacturer Dağıtımı
def assign_manufacturers_to_groups(collusion_groups):
    group_manus_map = {}
    for group_num, group_shops in enumerate(collusion_groups, start=1):
        common_manus = random.sample(manufacturers, 2)  # Ortak manufacturer'lar
        remaining_manus = [m for m in manufacturers if m not in common_manus]
        shop_manus = {}
        for shop in group_shops:
            extra_manus = random.sample(remaining_manus, random.choice([1, 2]))
            full_manus = common_manus + extra_manus
            shop_manus[shop] = full_manus
        group_manus_map[group_num] = {
            "group_shops": group_shops,
            "common_manus": common_manus,
            "shop_manus": shop_manus
        }
    return group_manus_map


# Zam Günlerini Seçme
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


# Collusion Ürünleri Seçme
def select_collusion_products(group_manus_map):
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

        # Ortak manufacturer'lar tarafından üretilen ürünleri belirle
        for manu in common_manus:
            manu_doc = manufacturer_cache[manu].get(sample_date)
            if not manu_doc:
                continue
            for i in range(1, 21):
                pname = manu_doc.get(f"Product {i}")
                if pname:
                    all_products.add(pname)

        all_products = list(all_products)

        # Ürünlerin %15–30'u collusion olarak seçilecek
        collusion_products = random.sample(all_products, max(1, int(len(all_products) * random.uniform(0.15, 0.30))))
        collusion_price_map = {p: round(random.uniform(5.0, 10.0), 2) / 100 for p in collusion_products}

        print(f"\n🔵 Grup {group_num} - Ortak Tarih: {sample_date.strftime('%Y-%m-%d')}")
        print(f"   ⭐ Lider Shop: {leader}")
        print(f"   🛒 Followerlar: {followers}")
        print(f"   ⏱️ Delay Günleri: {delays}")
        print(f"   🧱 Ortak Manufacturerlar: {common_manus}")
        print("   🧰 Shop-Specific Manufacturerlar:")
        for s, manus in shop_manus_map.items():
            print(f"     - {s}: {manus}")
        print(f"   📅 Zam Günleri: {[d.strftime('%Y-%m-%d') for d in zam_days]}")
        print(f"   🎯 Collusion Ürünleri: {collusion_products}\n")

        # Veriyi yazarken
        for shop in group_shops:
            shop_collection = db[shop]
            profit_variation = defaultdict(lambda: round(random.uniform(-0.1, 0.1), 3))
            previous_prices = {}
            bulk_ops = []

            for idx, date in enumerate(all_dates):
                effective_date = date + timedelta(days=delays[shop]) if shop != leader else date
                doc = {
                    "Date": date,
                    "Store Type": shop,
                    "Description": f"Generated collusion prices on {date.strftime('%Y-%m-%d')}"
                }
                shop_manus = shop_manus_map[shop]

                for manu in shop_manus:
                    base_date = date if shop == leader else date  # zam günü sabit
                    manu_data = manufacturer_cache[manu].get(base_date)
                    if not manu_data:
                        continue
                    manu_doc = {}

                    for i in range(1, 21):
                        pname = manu_data.get(f"Product {i}")
                        base_price_str = manu_data.get(f"Product {i} Price")
                        if not pname or not base_price_str:
                            continue
                        base_price = float(base_price_str.replace(",", "").replace(" TL", ""))

                        if pname in collusion_price_map and date in zam_days:
                            profit_pct = collusion_price_map[pname] * 100
                            final_price = base_price * (1 + collusion_price_map[pname])
                            previous_prices[pname] = final_price  # 💡 ÖNEMLİ: yeni fiyatı kaydet
                        else:
                            if idx == 0:
                                profit_pct = round(random.uniform(2.0, 12.0) + profit_variation[pname] * 100, 2)
                                final_price = base_price * (1 + profit_pct / 100)
                                previous_prices[pname] = final_price
                            elif date in zam_days:
                                profit_pct = round(random.uniform(2.0, 12.0) + profit_variation[pname] * 100, 2)
                                final_price = base_price * (1 + profit_pct / 100)
                                previous_prices[pname] = final_price
                            else:
                                final_price = previous_prices.get(pname, base_price)
                                profit_pct = None  # sadece bilgi

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
    collusion_groups = create_collusion_groups_from_list(list(range(1, 9)))
    group_structure = assign_manufacturers_to_groups(collusion_groups)
    select_collusion_products(group_structure)
