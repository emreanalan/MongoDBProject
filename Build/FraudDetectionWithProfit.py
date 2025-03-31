import pymongo
from datetime import datetime, timedelta

client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]

REFERENCE_COLLECTION = "Products"
THRESHOLD_PROFIT = 15  # %15'in üzeri şüpheli sayılacak

def detect_fraudulent_shops(start_date_str, end_date_str):
    start_date = datetime.fromisoformat(start_date_str)
    end_date = datetime.fromisoformat(end_date_str)

    fraudulent_shops = {}
    current_date = start_date

    while current_date <= end_date:
        ref_record = db[REFERENCE_COLLECTION].find_one({"Date": current_date})
        if not ref_record:
            current_date += timedelta(days=1)
            continue

        for shop_name in db.list_collection_names():
            if shop_name in [REFERENCE_COLLECTION, "system.indexes"]:
                continue

            shop_record = db[shop_name].find_one({"Date": current_date})
            if not shop_record or "Profit Percentage" not in shop_record:
                continue

            profit = shop_record["Profit Percentage"]
            if profit > THRESHOLD_PROFIT:
                if shop_name not in fraudulent_shops:
                    fraudulent_shops[shop_name] = {
                        "dates": [],
                        "max_profit": profit
                    }
                fraudulent_shops[shop_name]["dates"].append(str(current_date.date()))
                if profit > fraudulent_shops[shop_name]["max_profit"]:
                    fraudulent_shops[shop_name]["max_profit"] = profit

        current_date += timedelta(days=1)

    return fraudulent_shops

# Örnek kullanım:
if __name__ == "__main__":
    result = detect_fraudulent_shops("2025-03-01", "2025-03-26")

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
