import pymongo
from datetime import datetime, timedelta

def test_shops_relations(shops):
    client = pymongo.MongoClient(
        "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    db = client["DataSet"]

    # --- Her Shop'ın fiyat verisini çekelim
    shop_data = {}
    for shop in shops:
        collection = db[shop]
        records = list(collection.find({}).sort("Date", 1))
        date_to_prices = {}
        for record in records:
            date = record["Date"]
            prices = {}
            for manu_key in [k for k in record.keys() if k.endswith("Products")]:
                products = record[manu_key]
                for key in products:
                    if "Price" in key:
                        continue
                    num = key.split()[1]
                    pname = products.get(f"Product {num}")
                    pprice_str = products.get(f"Product {num} Price")
                    if pname and pprice_str:
                        price = float(pprice_str.replace(",", "").replace(" TL", ""))
                        prices[pname] = price
            date_to_prices[date] = prices
        shop_data[shop] = date_to_prices

    leader = shops[0]
    followers = shops[1:]

    print(f"\n🔵 Test Başladı: Leader = {leader}, Followers = {followers}")

    # --- Leader zam günlerini bulalım
    leader_dates = sorted(shop_data[leader].keys())
    previous_prices = {}
    zam_days = []

    for date in leader_dates:
        prices = shop_data[leader][date]
        for pname, price in prices.items():
            if pname in previous_prices:
                if abs(price - previous_prices[pname]) > 0.01:
                    zam_days.append(date)
                    break
            previous_prices[pname] = price

    zam_days = sorted(list(set(zam_days)))

    print(f"📅 Bulunan Zam Günleri: {[d.strftime('%Y-%m-%d') for d in zam_days]}")

    # --- Şimdi follower'lar doğru takip ediyor mu bakalım
    for follower in followers:
        follower_dates = sorted(shop_data[follower].keys())

        for zam_day in zam_days:
            # Follower hangi gün tepki vermiş?
            min_delay = None
            found = False

            for offset in range(1, 8):  # Delay max 7 gün olabilir
                target_day = zam_day + timedelta(days=offset)
                if target_day not in follower_dates:
                    continue

                leader_prices = shop_data[leader][zam_day]
                follower_prices = shop_data[follower][target_day]

                match_count = 0
                total_count = 0

                for pname, lprice in leader_prices.items():
                    fprice = follower_prices.get(pname)
                    if fprice is None:
                        continue
                    total_count += 1
                    if abs(fprice - lprice) <= 0.01:
                        match_count += 1

                if total_count > 0 and match_count / total_count > 0.8:  # %80'den fazlası eşleşiyorsa
                    min_delay = offset
                    found = True
                    break

            if not found:
                print(f"⚠️ {follower} mağazası {zam_day.strftime('%Y-%m-%d')} zam gününe tepki vermemiş.")
            else:
                print(f"✅ {follower} mağazası {zam_day.strftime('%Y-%m-%d')} zamını {min_delay} gün gecikmeli takip etmiş.")

    print("\n✅ Test Bitti.\n")

