import pymongo
from datetime import datetime, timedelta
from collections import defaultdict

# MongoDB Connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]

# Parameters
SIMILARITY_THRESHOLD = 0.999
MAX_DELAY_DAYS = 7
MAX_MISS_DAYS = 2


def clean_price(price_str):
    if isinstance(price_str, str):
        return float(price_str.replace(" TL", "").replace(",", ""))
    return price_str


def preload_data(start_date, end_date, shop_names):
    data = defaultdict(dict)
    current_date = start_date
    while current_date <= end_date:
        for shop in shop_names:
            record = db[shop].find_one({"Date": current_date})
            if record:
                for group_key in record:
                    if group_key.endswith("Products") and isinstance(record[group_key], dict):
                        products = {}
                        group = record[group_key]
                        for key in group:
                            if key.endswith("Price"):
                                number = key.split(" ")[1]
                                name_key = f"Product {number}"
                                name = group.get(name_key)
                                price = clean_price(group[key])
                                if name and price is not None:
                                    products[name] = price
                        data[(shop, group_key)][current_date] = (products, record.get("Profit Percentage"))
        current_date += timedelta(days=1)
    return data


def find_collusion(start_date_str, end_date_str):
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    shop_names = [name for name in db.list_collection_names() if name not in ["Products", "system.indexes"]]
    shop_data = preload_data(start_date, end_date, shop_names)

    collusion_records = []
    current_date = start_date

    while current_date <= end_date:
        manufacturer_data = defaultdict(list)

        for (shop, manufacturer), date_data in shop_data.items():
            if current_date in date_data:
                prices, profit = date_data[current_date]
                manufacturer_data[manufacturer].append((shop, profit))

        for manufacturer, shops_info in manufacturer_data.items():
            if len(shops_info) < 2:
                continue

            leader_shop, leader_profit = shops_info[0]
            followers = []

            for follower_shop, follower_profit in shops_info[1:]:
                if follower_profit == leader_profit:
                    followers.append(follower_shop)

            if followers:
                collusion_records.append({
                    "Leader": leader_shop,
                    "Followers": followers,
                    "Manufacturer": manufacturer,
                    "Start Date": current_date
                })

        current_date += timedelta(days=1)

    return group_collusion_periods(collusion_records)


def group_collusion_periods(records):
    grouped = defaultdict(lambda: {"Followers": set(), "Dates": []})

    for record in records:
        key = (record["Leader"], tuple(sorted(record["Followers"])), record["Manufacturer"])
        grouped[key]["Dates"].append(record["Start Date"])

    final_result = []
    for (leader, followers, manufacturer), data in grouped.items():
        dates = sorted(data["Dates"])
        if not dates:
            continue

        start_date = dates[0]
        last_date = dates[0]
        temp_dates = []

        for current_date in dates[1:]:
            if (current_date - last_date).days <= MAX_MISS_DAYS + 1:
                temp_dates.append(current_date)
            else:
                if temp_dates:
                    final_result.append({
                        "Leader": leader,
                        "Followers": list(followers),
                        "Manufacturer": manufacturer,
                        "Start Date": str(start_date.date()),
                        "End Date": str(last_date.date()),
                        "Duration (days)": (last_date - start_date).days + 1
                    })
                start_date = current_date
                temp_dates = []
            last_date = current_date

        if temp_dates or start_date == last_date:
            final_result.append({
                "Leader": leader,
                "Followers": list(followers),
                "Manufacturer": manufacturer,
                "Start Date": str(start_date.date()),
                "End Date": str(last_date.date()),
                "Duration (days)": (last_date - start_date).days + 1
            })

    return final_result


if __name__ == "__main__":
    result = find_collusion("2025-01-01", "2025-04-18")

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))