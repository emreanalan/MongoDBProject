import pymongo
from datetime import datetime, timedelta

# MongoDB bağlantısı
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]

def get_last_inserted_date(collection):
    last_record = collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record['Date']
    return None

def db_shop(manufacturer_name, shop_name, profit_percentage, date_str):
    manufacturer_collection = db[manufacturer_name]
    shop_collection = db[shop_name]

    date = datetime.fromisoformat(date_str)

    record = manufacturer_collection.find_one({"Date": date})
    if not record:
        print(f"No data found for {manufacturer_name} on {date}.")
        return

    shop_record = shop_collection.find_one({"Date": date}) or {
        "Date": date,
        "Profit Percentage": profit_percentage,
        "Store Type": shop_name,
        "Description": f"Product prices for {shop_name} as of {date}.",
    }

    product_group = f"{manufacturer_name} Products"
    if product_group not in shop_record:
        shop_record[product_group] = {}

    product_keys = [key for key in record.keys() if key.startswith("Product ")]

    product_counter = 1
    for key in product_keys:
        if "Price" in key:
            price = float(record[key].replace(" TL", "").replace(",", ""))
            new_price = price * (1 + profit_percentage / 100)

            shop_record[product_group][f"Product {product_counter}"] = record[f"Product {product_counter}"]
            shop_record[product_group][f"Product {product_counter} Price"] = f"{new_price:,.2f} TL"
            product_counter += 1

    new_shop_record = {
        "Date": shop_record["Date"],
        "Profit Percentage": shop_record["Profit Percentage"],
        "Store Type": shop_record["Store Type"],
        "Description": shop_record["Description"],
    }

    for key in sorted(shop_record.keys()):
        if key.endswith("Products"):
            new_shop_record[key] = shop_record[key]

    existing_record = shop_collection.find_one({"Date": date})

    if existing_record:
        shop_collection.update_one({"_id": existing_record["_id"]}, {"$set": new_shop_record})
        print(f"Updated record for {shop_name} on {date}.")
    else:
        shop_collection.insert_one(new_shop_record)
        print(f"Inserted new record for {shop_name} on {date}.")

def collusion(begin_date, end_date, manufacturer_name, leader_profit_percentage, follower_profit_percentage, day_delay, leader, followers, fallback_date=None):
    current_date = datetime.fromisoformat(begin_date)
    end_date_dt = datetime.fromisoformat(end_date)

    # Fallback kayıtları yükle (varsa)
    fallback_records = {}
    if fallback_date:
        for follower in followers:
            fallback_record = db[follower].find_one({"Date": datetime.fromisoformat(fallback_date)})
            if fallback_record:
                fallback_records[follower] = fallback_record

    previous_records = {follower: None for follower in followers}

    while current_date <= end_date_dt:
        # Leader mağaza o gün kaydını atıyor
        db_shop(manufacturer_name, leader, leader_profit_percentage, current_date.isoformat())

        # Followers day_delay gün sonra kayıt atacak
        follower_date = current_date + timedelta(days=day_delay)

        if follower_date <= end_date_dt:
            for follower in followers:
                db_shop(manufacturer_name, follower, follower_profit_percentage, follower_date.isoformat())

                # Eğer veri eksikse fallback uygula
                record = db[follower].find_one({"Date": follower_date})
                if not record:
                    if previous_records[follower]:
                        new_record = previous_records[follower].copy()
                        new_record["Date"] = follower_date
                        if "_id" in new_record:
                            del new_record["_id"]
                        db[follower].insert_one(new_record)
                        print(f"Inserted missing record for {follower} on {follower_date}.")
                    elif fallback_records.get(follower):
                        new_record = fallback_records[follower].copy()
                        new_record["Date"] = follower_date
                        if "_id" in new_record:
                            del new_record["_id"]
                        db[follower].insert_one(new_record)
                        print(f"Inserted missing record for {follower} using fallback on {follower_date}.")
                    else:
                        print(f"No previous or fallback record to fill for {follower} on {follower_date}.")
                else:
                    previous_records[follower] = record

        current_date += timedelta(days=1)

# -------------------------------------------------------
# 📋 Buradan aşağısı kullanım örnekleri
# (Sana örnek inputlar da hazırladım!)
# -------------------------------------------------------

#YourElectrician lider, diğerleri takipçi
collusion(
    "2025-01-01",
    "2025-02-01",
    "ELectronicMan",
    leader_profit_percentage=5,
    follower_profit_percentage=5,
    day_delay=5,
    leader="YourElectrician",
    followers=["MyElectrician", "HisElectrician"]
)

collusion(
    "2025-02-02",
    "2025-03-01",
    "ELectronicMan",
    leader_profit_percentage=7,
    follower_profit_percentage=7,
    day_delay=4,
    leader="YourElectrician",
    followers=["MyElectrician", "HisElectrician"],
    fallback_date="2025-02-18"
)

collusion(
    "2025-03-02",
    "2025-04-20",
    "ELectronicMan",
    leader_profit_percentage=10,
    follower_profit_percentage=10,
    day_delay=3,
    leader="YourElectrician",
    followers=["MyElectrician", "HisElectrician"],
    fallback_date="2025-03-18"
)

collusion(
    "2025-01-01",
    "2025-02-01",
    "HomeELectricMan",
    leader_profit_percentage=5,
    follower_profit_percentage=5,
    day_delay=5,
    leader="YourElectrician",
    followers=["MyElectrician", "HisElectrician"]
)

collusion(
    "2025-02-02",
    "2025-03-01",
    "HomeELectricMan",
    leader_profit_percentage=7,
    follower_profit_percentage=7,
    day_delay=4,
    leader="YourElectrician",
    followers=["MyElectrician", "HisElectrician"],
    fallback_date="2025-02-18"
)

collusion(
    "2025-03-02",
    "2025-04-20",
    "HomeELectricMan",
    leader_profit_percentage=10,
    follower_profit_percentage=10,
    day_delay=3,
    leader="YourElectrician",
    followers=["MyElectrician", "HisElectrician"],
    fallback_date="2025-03-18"
)

