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
manufacturer_product_profit_cache = {}

start_date = datetime(2025, 1, 1)
all_dates = [start_date + timedelta(days=i) for i in range(115)]

for manu in manufacturers:
    print(f"  🔹 {manu} cache'leniyor...")
    manu_cursor = db[manu].find({}, {"_id": 0})
    manu_data = {}
    for record in manu_cursor:
        date = record["Date"]
        manu_data[date] = record
        for k in record:
            if k.startswith("Product ") and "Price" not in k:
                pname = record[k]
                if manu not in manufacturer_product_profit_cache:
                    manufacturer_product_profit_cache[manu] = {}
                if pname not in manufacturer_product_profit_cache[manu]:
                    manufacturer_product_profit_cache[manu][pname] = round(random.uniform(2.0, 12.0), 2)
    manufacturer_cache[manu] = manu_data
print("✅ Manufacturer cache tamamlandı.\n")

def generate_shop_documents(shop_ids, is_collusion=False):
    if is_collusion:
        print("\n🧠 Ortak ürünler belirleniyor ve collusion ürünleri seçiliyor...\n")
        groups = create_collusion_groups_from_list(list(shop_ids))
        group_map = assign_manufacturers_to_groups(groups)
        generate_collusion_shops(group_map)
    else:
        print("\n🚀 ShopsDataSet oluşturuluyor...\n")
        generate_normal_shops(shop_ids)

def create_collusion_groups_from_list(shop_ids):
    random.shuffle(shop_ids)
    groups = []
    idx = 0
    while idx < len(shop_ids):
        #group_size = random.choice([3, 4, 5])
        group_size = 10
        group = [f"Shop {i}" for i in shop_ids[idx:idx + group_size]]
        if len(group) >= 3:
            groups.append(group)
            idx += group_size
        else:
            if groups:
                groups[-1].extend([f"Shop {i}" for i in shop_ids[idx:]])
            break
    return groups

def assign_manufacturers_to_groups(groups):
    group_manus_map = {}
    for group_num, group_shops in enumerate(groups, start=1):
        common_manus = random.sample(manufacturers, 2)
        remaining_manus = [m for m in manufacturers if m not in common_manus]
        # Her shop en az 2 üreticiye sahip olmalı: 2 ortak + 1-2 ekstra = 3-4 toplam
        shop_manus = {}
        for shop in group_shops:
            num_extra = random.randint(1, 2)
            # Amaç: toplamda 3 veya 4 üretici olmalı
            extra_manus = random.sample(remaining_manus, k=num_extra)
            full_manus = list(set(common_manus + extra_manus))
            shop_manus[shop] = full_manus
            print(f"      🔸 {shop} için tüm manufacturerlar: {full_manus}")
        print(f"   🧱 Ortak Manufacturerlar: {common_manus}")
        group_manus_map[group_num] = {
            "group_shops": group_shops,
            "common_manus": common_manus,
            "shop_manus": shop_manus
        }
    return group_manus_map

def generate_normal_shops(shop_ids):
    for shop_num in shop_ids:
        shop_name = f"Shop {shop_num}"
        shop_collection = db[shop_name]
        selected_manus = random.sample(manufacturers, random.choice([2, 3]))
        print(f"🔵 {shop_name} için seçilen manufacturerlar: {selected_manus}")
        zam_days = sorted(random.sample(range(5, 110), k=random.randint(2, 5)))
        print(f"  📅 {shop_name} zam günleri: {[all_dates[day].strftime('%Y-%m-%d') for day in zam_days]}")
        bulk_ops = []
        previous_prices = {}
        profit_variation = defaultdict(lambda: round(random.uniform(-0.02, 0.02), 3))

        for date_idx, current_date in enumerate(all_dates):
            doc = {
                "Date": current_date,
                "Store Type": shop_name,
                "Description": f"Generated prices for {shop_name} on {current_date.strftime('%Y-%m-%d')}"
            }
            for manu in selected_manus:
                manu_data = manufacturer_cache[manu].get(current_date)
                if not manu_data:
                    continue
                manu_doc = {}
                for i in range(1, 21):
                    pname = manu_data.get(f"Product {i}")
                    pprice = manu_data.get(f"Product {i} Price")
                    if not pname or not pprice:
                        continue
                    base_price = float(pprice.replace(",", "").replace(" TL", ""))
                    base_profit = manufacturer_product_profit_cache[manu][pname]
                    adj_profit = round(base_profit + profit_variation[pname] * 100, 2)
                    if date_idx == 0 or date_idx in zam_days:
                        final_price = base_price * (1 + adj_profit / 100)
                        previous_prices[pname] = final_price
                    else:
                        final_price = previous_prices.get(pname, base_price * (1 + adj_profit / 100))
                    manu_doc[f"Product {i}"] = pname
                    manu_doc[f"Product {i} Manufacturer Price"] = f"{base_price:,.2f} TL"
                    manu_doc[f"Product {i} Shop Profit %"] = adj_profit
                    manu_doc[f"Product {i} Price"] = f"{final_price:,.2f} TL"
                if manu_doc:
                    doc[f"{manu} Products"] = manu_doc
            bulk_ops.append(pymongo.UpdateOne({"Date": current_date}, {"$set": doc}, upsert=True))
        if bulk_ops:
            shop_collection.bulk_write(bulk_ops)
            print(f"✅ {shop_name} için {len(bulk_ops)} kayıt eklendi.\n")
        else:
            print(f"⚠️ {shop_name} için hiç veri eklenmedi.\n")
    print("\n✅ Tüm ShopsDataSet kayıtları başarıyla tamamlandı!")


def generate_collusion_shops(group_map):
    for group_num, group_data in group_map.items():
        group_shops = group_data["group_shops"]
        common_manus = group_data["common_manus"]
        shop_manus_map = group_data["shop_manus"]
        leader = group_shops[0]
        delays = {shop: (0 if shop == leader else random.randint(1, 4)) for shop in group_shops}

        zam_days = []
        while len(zam_days) < random.randint(3, 6):
            aday = random.randint(7, 110)
            if all(abs(aday - mevcut) >= 10 for mevcut in zam_days):
                zam_days.append(aday)
        zam_days.sort()

        # Her zam günü için ortak ama farklı zam oranları üret
        zam_oranlari = {z_day: round(random.uniform(0.055, 0.075), 5) for z_day in zam_days}
        sapma_degeri_map = {shop: round(random.uniform(-0.0005, 0.0005), 4) for shop in group_shops}

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

        collusion_products = random.sample(list(all_products), max(1, int(len(all_products) * random.uniform(0.15, 0.30))))

        collusion_profit_map = {}
        for pname in collusion_products:
            collusion_profit_map[pname] = round(random.uniform(0.08, 0.12), 5)

        shop_start_prices = {shop: {} for shop in group_shops}
        for shop in group_shops:
            sapma = sapma_degeri_map[shop]
            for pname in collusion_products:
                for manu in common_manus:
                    manu_data = manufacturer_cache[manu].get(sample_date)
                    if not manu_data:
                        continue
                    for i in range(1, 21):
                        p = manu_data.get(f"Product {i}")
                        price_str = manu_data.get(f"Product {i} Price")
                        if p == pname and price_str:
                            manu_price = float(price_str.replace(",", "").replace(" TL", ""))
                            profit_orani = collusion_profit_map[pname]
                            base_price = manu_price * (1 + profit_orani)
                            final_price = round(base_price * (1 + sapma), 2)
                            shop_start_prices[shop][pname] = final_price
                            break
                    if pname in shop_start_prices[shop]:
                        break

        dynamic_start_prices = {}
        for manu in common_manus:
            manu_data = manufacturer_cache[manu].get(sample_date)
            if not manu_data:
                continue
            for i in range(1, 21):
                pname = manu_data.get(f"Product {i}")
                pprice = manu_data.get(f"Product {i} Price")
                if pname and pprice and pname not in collusion_products:
                    base_price = float(pprice.replace(",", "").replace(" TL", ""))
                    dynamic_start_prices[pname] = base_price

        zam_gunleri_str = [all_dates[z].strftime('%Y-%m-%d') for z in zam_days]

        print(f"\n🔵 Grup {group_num} - Ortak Tarih: {sample_date.strftime('%Y-%m-%d')}")
        print(f"   ⭐ Lider Shop: {leader}")
        print(f"   ⏱️ Delay Günleri: {delays}")
        print(f"   🧱 Ortak Manufacturerlar: {common_manus}")
        print(f"   📅 Zam Günleri (lider için): {zam_gunleri_str}")
        print(f"   🎯 Collusion ürünleri: {collusion_products}\n")

        for shop in group_shops:
            bulk_ops = []
            previous_prices = shop_start_prices[shop].copy()
            shop_collection = db[shop]

            for day_index, date in enumerate(all_dates):
                doc = {
                    "Date": date,
                    "Store Type": shop,
                    "Description": f"Generated collusion prices on {date.strftime('%Y-%m-%d')}"
                }

                for manu in shop_manus_map[shop]:
                    manu_data = manufacturer_cache[manu].get(date)
                    if not manu_data:
                        continue

                    manu_doc = {}

                    for i in range(1, 21):
                        pname = manu_data.get(f"Product {i}")
                        pprice_str = manu_data.get(f"Product {i} Price")
                        if not pname or not pprice_str:
                            continue

                        if pname in collusion_products:
                            delay = delays[shop]
                            for z_day in zam_days:
                                if day_index == z_day + delay:
                                    old_price = previous_prices[pname]
                                    zam_orani = zam_oranlari[z_day]
                                    new_price = round(old_price * (1 + zam_orani), 2)
                                    sapma = sapma_degeri_map[shop]
                                    new_price = round(new_price * (1 + sapma), 2)  # shop'a özel sabit sapma
                                    previous_prices[pname] = new_price
                                    break

                            final_price = previous_prices[pname]
                            profit_pct = collusion_profit_map[pname] * 100

                        else:
                            # COLLUSION DIŞI ÜRÜNLER ARTIK NORMAL MAĞAZA MANTIĞIYLA DAVRANACAK
                            base_price = float(pprice_str.replace(",", "").replace(" TL", ""))
                            if pname not in previous_prices:
                                base_profit = manufacturer_product_profit_cache[manu][pname]
                                profit_variation = round(random.uniform(-0.02, 0.02), 3)
                                adj_profit = round(base_profit + profit_variation * 100, 2)
                                final_price = base_price * (1 + adj_profit / 100)
                                previous_prices[pname] = final_price
                                profit_pct = adj_profit
                            elif day_index in zam_days:
                                base_profit = manufacturer_product_profit_cache[manu][pname]
                                profit_variation = round(random.uniform(-0.02, 0.02), 3)
                                adj_profit = round(base_profit + profit_variation * 100, 2)
                                final_price = base_price * (1 + adj_profit / 100)
                                previous_prices[pname] = final_price
                                profit_pct = adj_profit
                            else:
                                final_price = previous_prices[pname]
                                profit_pct = (final_price - base_price) / base_price * 100

                        manu_doc[f"Product {i}"] = pname
                        manu_doc[f"Product {i} Manufacturer Price"] = pprice_str
                        manu_doc[f"Product {i} Price"] = f"{final_price:,.2f} TL"
                        manu_doc[f"Product {i} Shop Profit %"] = profit_pct

                    if manu_doc:
                        doc[f"{manu} Products"] = manu_doc

                bulk_ops.append(pymongo.UpdateOne({"Date": date}, {"$set": doc}, upsert=True))
                if len(bulk_ops) >= 30:
                    shop_collection.bulk_write(bulk_ops)
                    bulk_ops = []

            if bulk_ops:
                shop_collection.bulk_write(bulk_ops)
            print(f"✅ {shop} collusion verisi oluşturuldu.")







all_shops = list(range(1, 401))
random.shuffle(all_shops)

# İlk 200 tanesi normal, kalan 200 tanesi collusion olarak ayrılır
generate_shop_documents(all_shops[:200], is_collusion=False)
generate_shop_documents(all_shops[200:], is_collusion=True)