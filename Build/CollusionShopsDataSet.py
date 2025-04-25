import pymongo
import random
from datetime import datetime, timedelta
from copy import deepcopy

# MongoDB connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

products_collection = db["Products"]
manufacturers = [f"Man{i}" for i in range(1, 26)]

# Product cache (hız için)
product_cursor = products_collection.find({}, {"Product Name": 1, "Date": 1, "Cost": 1})
product_cache = {(p["Product Name"], p["Date"]): p["Cost"] for p in product_cursor}

# 115 gün tarih listesi
start_date = datetime(2025, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(115)]


def select_zam_days():
    zam_days = []
    possible_days = list(range(7, len(dates)))  # İlk 7 günü atlıyoruz

    while True:
        if len(zam_days) >= 6:
            break
        if not possible_days:
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

    zam_days = sorted(zam_days)
    return zam_days


def create_collusion_group(leader_shop, follower_shops):
    selected_manufacturers = random.sample(manufacturers, k=random.choice([2, 3]))
    print(f"\n{leader_shop} collusion grubu --> {selected_manufacturers}")

    leader_col = db[leader_shop]
    follower_cols = {shop: db[shop] for shop in follower_shops}

    follower_delays = {shop: random.randint(1, 7) for shop in follower_shops}
    print(f"Delayler: {follower_delays}")

    zam_days = select_zam_days()
    print(f"Zam Günleri: {[dates[d].strftime('%Y-%m-%d') for d in zam_days]}")

    leader_prices = {}
    previous_docs = {follower: None for follower in follower_shops}

    for day_idx, current_date in enumerate(dates):
        doc = {
            "Date": current_date,
            "Store Type": leader_shop,
            "Description": f"Prices for {leader_shop} on {current_date.strftime('%Y-%m-%d')}"
        }

        for manu in selected_manufacturers:
            manu_doc = {}
            manu_data = db[manu].find_one({"Date": current_date})
            if not manu_data:
                continue

            product_keys = sorted(
                [k for k in manu_data if k.startswith("Product ") and "Price" not in k],
                key=lambda k: int(k.split()[1])
            )

            for i, key in enumerate(product_keys):
                pname = manu_data[key]
                base_cost_str = product_cache.get((pname, current_date))
                if not base_cost_str:
                    continue

                base = float(base_cost_str.replace(" TL", "").replace(",", ""))

                if day_idx in zam_days and random.random() < random.uniform(0.2, 0.5):
                    profit = random.randint(2, 12)
                    final = base * (1 + profit / 100)
                else:
                    final = leader_prices.get(pname, base)

                leader_prices[pname] = final

                manu_doc[f"Product {i + 1}"] = pname
                manu_doc[f"Product {i + 1} Price"] = f"{final:,.2f} TL"

            if manu_doc:
                doc[f"{manu} Products"] = manu_doc

        leader_col.update_one({"Date": current_date}, {"$set": doc}, upsert=True)

        # Followers
        for follower, f_col in follower_cols.items():
            delay = follower_delays[follower]
            delayed_date = current_date + timedelta(days=delay)

            if delayed_date > dates[-1]:
                continue

            if previous_docs[follower] is None:
                # İlk veri
                follower_doc = deepcopy(doc)
                follower_doc["Date"] = delayed_date
                follower_doc["Store Type"] = follower
                follower_doc[
                    "Description"] = f"[Following {leader_shop}] Prices for {follower} on {delayed_date.strftime('%Y-%m-%d')}"
                f_col.update_one({"Date": delayed_date}, {"$set": follower_doc}, upsert=True)
                previous_docs[follower] = follower_doc
            else:
                # Aradaki günler için aynı veriyi taşı
                last_date = previous_docs[follower]["Date"]
                while last_date < delayed_date:
                    carry_doc = deepcopy(previous_docs[follower])
                    carry_doc["Date"] = last_date + timedelta(days=1)
                    f_col.update_one({"Date": carry_doc["Date"]}, {"$set": carry_doc}, upsert=True)
                    last_date = carry_doc["Date"]

                follower_doc = deepcopy(doc)
                follower_doc["Date"] = delayed_date
                follower_doc["Store Type"] = follower
                follower_doc[
                    "Description"] = f"[Following {leader_shop}] Prices for {follower} on {delayed_date.strftime('%Y-%m-%d')}"
                f_col.update_one({"Date": delayed_date}, {"$set": follower_doc}, upsert=True)
                previous_docs[follower] = follower_doc

    print(f"✅ {leader_shop} grubu tamamlandı.")


def generate_collusion_groups(start_shop=91, end_shop=160, n_groups=70):
    available_shops = list(range(start_shop, end_shop + 1))
    random.shuffle(available_shops)

    for _ in range(n_groups):
        if len(available_shops) < 3:
            break

        group_size = random.choice([3, 4, 5])
        if len(available_shops) < group_size:
            group_size = len(available_shops)

        group_shops = available_shops[:group_size]
        available_shops = available_shops[group_size:]

        leader = f"Shop {group_shops[0]}"
        followers = [f"Shop {shop}" for shop in group_shops[1:]]

        print(f"🚀 Collusion Grubu: {leader} ➔ {followers}")
        create_collusion_group(leader, followers)


generate_collusion_groups()
