import pandas as pd
import random
import pymongo
from datetime import datetime, timedelta

# MongoDB connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

collections = {
    "Aluminum": db["Aluminum/TRY"],
    "Copper": db["Copper/TRY"],
    "Gold": db["Gold/TRY"],
    "Silver": db["Silver/TRY"],
    "USD_TRY": db["USD/TRY"],
    "EUR_TRY": db["EUR/TRY"],
    "Elektrik_Ucreti": db["Elektrik"],
    "Asgari_Ucret": db["Asgari_Ucret"],
    "DogalGaz_Ucreti": db["DogalGaz"],
    "Ham_Petrol_Fiyati": db["Brent/TRY"],
}


# Helper functions
def clean_price(price_str):
    if isinstance(price_str, str):
        price_str = price_str.replace(" TL", "").replace(",", ".")
        if price_str.count(".") > 1:
            price_str = price_str.replace(".", "", price_str.count(".") - 1)
        try:
            return float(price_str)
        except ValueError:
            return None
    return None


def fetch_data(collection_name, price_column="Price"):
    collection = collections[collection_name]
    cursor = collection.find({}, {"Date": 1, price_column: 1}).sort("Date", pymongo.ASCENDING)
    data = pd.DataFrame(list(cursor))
    data["Date"] = pd.to_datetime(data["Date"]).dt.date
    data[price_column] = data[price_column].apply(clean_price)
    return data


def fetch_fixed_price(collection, year):
    price_record = collection.find_one({"Date": datetime(year, 1, 1)})
    if price_record:
        return clean_price(price_record["Price"])
    return None


def get_latest_price(data, date, price_column="Price"):
    recent_data = data[data["Date"] <= date]
    if not recent_data.empty:
        return recent_data.iloc[-1][price_column]
    return None


def calculate_daily_costs(product_name, materials, start_date,
                          gold_data, copper_data, aluminum_data, silver_data,
                          usd_try_data, eur_try_data, ham_petrol_data,
                          electricity_price, asgari_ucret_price, dogalgaz_price):
    daily_costs = []

    for date in pd.date_range(start=start_date, end=datetime.now(), freq="D").date:
        gold_cost = get_latest_price(gold_data, date)
        copper_cost = get_latest_price(copper_data, date)
        aluminum_cost = get_latest_price(aluminum_data, date)
        silver_cost = get_latest_price(silver_data, date)
        ham_petrol_cost = get_latest_price(ham_petrol_data, date)
        usd_to_try = get_latest_price(usd_try_data, date)
        eur_to_try = get_latest_price(eur_try_data, date)

        if all([gold_cost, copper_cost, aluminum_cost, silver_cost, ham_petrol_cost, usd_to_try, eur_to_try,
                electricity_price, asgari_ucret_price, dogalgaz_price]):
            total_cost = (
                    aluminum_cost * materials.get("Aluminum 1Kg", 0)
                    + gold_cost * materials.get("Gold 1Kg", 0)
                    + copper_cost * materials.get("Copper 1Kg", 0)
                    + silver_cost * materials.get("Silver 1Kg", 0)
                    + ham_petrol_cost * materials.get("Ham_Petrol_Fiyati 1L", 0)
                    + electricity_price * materials.get("Elektrik_Ucreti 1kW", 0)
                    + (asgari_ucret_price / 30) * materials.get("Asgari_Ucret 1 iş günü", 0)
                    + dogalgaz_price * materials.get("Dogal_Gaz 100m^3", 0)
                    + usd_to_try * materials.get("USD", 0)
                    + eur_to_try * materials.get("EUR", 0)
            )
            total_cost = round(total_cost, 2)
            daily_costs.append({
                "Date": datetime.combine(date, datetime.min.time()),
                "Cost": f"{total_cost:,.2f} TL",
                "Materials": ", ".join([f"{v} {k}" for k, v in materials.items() if v > 0]),
                "Description": f"{date.day}/{date.month}/{date.year} cost of {product_name}"
            })

    return daily_costs


def insert_daily_costs(product_name, materials,
                       gold_data, copper_data, aluminum_data, silver_data,
                       usd_try_data, eur_try_data, ham_petrol_data,
                       electricity_price, asgari_ucret_price, dogalgaz_price):
    product_collection = db[product_name]

    start_date = datetime(2025, 1, 1).date()
    daily_costs = calculate_daily_costs(product_name, materials, start_date,
                                        gold_data, copper_data, aluminum_data, silver_data,
                                        usd_try_data, eur_try_data, ham_petrol_data,
                                        electricity_price, asgari_ucret_price, dogalgaz_price)

    if daily_costs:
        product_collection.insert_many(daily_costs)
        print(f"Inserted {len(daily_costs)} days for {product_name}")
    else:
        print(f"No data inserted for {product_name}")


# Preload datasets
print("Fetching market data...")
gold_data = fetch_data("Gold")
copper_data = fetch_data("Copper")
aluminum_data = fetch_data("Aluminum")
silver_data = fetch_data("Silver")
usd_try_data = fetch_data("USD_TRY")
eur_try_data = fetch_data("EUR_TRY")
ham_petrol_data = fetch_data("Ham_Petrol_Fiyati")
electricity_price = fetch_fixed_price(collections["Elektrik_Ucreti"], 2025)
asgari_ucret_price = fetch_fixed_price(collections["Asgari_Ucret"], 2025)
dogalgaz_price = fetch_fixed_price(collections["DogalGaz_Ucreti"], 2025)

print("Starting insertion...")

# Create 500 products
for i in range(419, 501):
    product_name = f"Product {i}"
    materials = {
        "Aluminum 1Kg": round(random.uniform(0, 0.5), 3) if random.random() > 0.3 else 0,
        "Copper 1Kg": round(random.uniform(0, 0.3), 3) if random.random() > 0.3 else 0,
        "Gold 1Kg": round(random.uniform(0, 0.05), 3) if random.random() > 0.5 else 0,
        "Silver 1Kg": round(random.uniform(0, 0.05), 3) if random.random() > 0.5 else 0,
        "Ham_Petrol_Fiyati 1L": round(random.uniform(0, 2), 2),
        "Elektrik_Ucreti 1kW": round(random.uniform(0, 10), 2),
        "Asgari_Ucret 1 iş günü": round(random.uniform(0, 1), 2),
        "Dogal_Gaz 100m^3": round(random.uniform(0, 0.05), 3),
        "USD": round(random.uniform(0, 5), 2) if random.random() > 0.5 else 0,
        "EUR": round(random.uniform(0, 5), 2) if random.random() > 0.5 else 0
    }
    insert_daily_costs(product_name, materials,
                       gold_data, copper_data, aluminum_data, silver_data,
                       usd_try_data, eur_try_data, ham_petrol_data,
                       electricity_price, asgari_ucret_price, dogalgaz_price)

print("✅ Finished inserting 500 products.")


# copperCable_materials = {
#     "Aluminum 1Kg": 0,
#     "Copper 1Kg": 0.05,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1,
# }
# GoldCable_materials = {
#     "Aluminum 1Kg": 0,
#     "Copper 1Kg": 0.01,
#     "Gold 1Kg": 0.005,
#     "Silver 1Kg": 0,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1,
# }
# USBCable_materials = {
#     "Aluminum 1Kg": 0.01,
#     "Copper 1Kg": 0.03,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1
# }
# silverCable_materials = {
#     "Aluminum 1Kg": 0.01,
#     "Copper 1Kg": 0,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 0,
#     "EUR": 1
# }
# toy_Car_materials = {
#     "Aluminum 1Kg": 0.01,
#     "Copper 1Kg": 0.001,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 0,
#     "EUR": 1
# }
# toy_AliminumGun_materials = {
#     "Aluminum 1Kg": 0.03,
#     "Copper 1Kg": 0,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 0,
#     "EUR": 2
# }
# toy_TeddyBear_materials = {
#     "Aluminum 1Kg": 0.01,
#     "Copper 1Kg": 0.001,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 30,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.1,
#     "USD": 10,
#     "EUR": 0
# }
# gamePad_materials = {
#     "Aluminum 1Kg": 0.01,
#     "Copper 1Kg": 0.001,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.001,
#     "Ham_Petrol_Fiyati 1L": 10,
#     "Elektrik_Ucreti 1kW": 100,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 5,
#     "EUR": 0
# }
# headphones_materials = {
#     "Aluminum 1Kg": 0.05,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 0.5,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1
# }
# laptop_materials = {
#     "Aluminum 1Kg": 0.5,
#     "Copper 1Kg": 0.3,
#     "Gold 1Kg": 0.01,
#     "Silver 1Kg": 0.05,
#     "Ham_Petrol_Fiyati 1L": 0.8,
#     "Elektrik_Ucreti 1kW": 3,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.02,
#     "USD": 1,
#     "EUR": 1
# }
# smartphone_materials = {
#     "Aluminum 1Kg": 0.3,
#     "Copper 1Kg": 0.2,
#     "Gold 1Kg": 0.05,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 1,
#     "Elektrik_Ucreti 1kW": 2,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.015,
#     "USD": 1,
#     "EUR": 1
# }
# tablet_materials = {
#     "Aluminum 1Kg": 0.4,
#     "Copper 1Kg": 0.25,
#     "Gold 1Kg": 0.03,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 0.6,
#     "Elektrik_Ucreti 1kW": 2,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1
# }
# smartwatch_materials = {
#     "Aluminum 1Kg": 0.1,
#     "Copper 1Kg": 0.05,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.01,
#     "Ham_Petrol_Fiyati 1L": 0.5,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1
# }
# gamingMouse_materials = {
#     "Aluminum 1Kg": 0.05,
#     "Copper 1Kg": 0.02,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.01,
#     "Ham_Petrol_Fiyati 1L": 0.3,
#     "Elektrik_Ucreti 1kW": 0.5,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.005,
#     "USD": 0.8,
#     "EUR": 0.9
# }
# electricFan_materials = {
#     "Aluminum 1Kg": 0.1,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.01,
#     "Ham_Petrol_Fiyati 1L": 0.7,
#     "Elektrik_Ucreti 1kW": 0.6,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.02,
#     "USD": 1,
#     "EUR": 1
# }
# microwave_materials = {
#     "Aluminum 1Kg": 0.2,
#     "Copper 1Kg": 0.15,
#     "Gold 1Kg": 0.02,
#     "Silver 1Kg": 0.05,
#     "Ham_Petrol_Fiyati 1L": 0.9,
#     "Elektrik_Ucreti 1kW": 1.5,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1
# }
# vacuumCleaner_materials = {
#     "Aluminum 1Kg": 0.25,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 0.6,
#     "Elektrik_Ucreti 1kW": 1.2,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.015,
#     "USD": 0.9,
#     "EUR": 1
# }
# airConditioner_materials = {
#     "Aluminum 1Kg": 0.5,
#     "Copper 1Kg": 0.3,
#     "Gold 1Kg": 0.05,
#     "Silver 1Kg": 0.1,
#     "Ham_Petrol_Fiyati 1L": 0.8,
#     "Elektrik_Ucreti 1kW": 3,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.02,
#     "USD": 1,
#     "EUR": 1
# }
# television_materials = {
#     "Aluminum 1Kg": 0.6,
#     "Copper 1Kg": 0.5,
#     "Gold 1Kg": 0.1,
#     "Silver 1Kg": 0.1,
#     "Ham_Petrol_Fiyati 1L": 1.5,
#     "Elektrik_Ucreti 1kW": 2,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.015,
#     "USD": 1,
#     "EUR": 1
# }
# refrigerator_materials = {
#     "Aluminum 1Kg": 0.3,
#     "Copper 1Kg": 0.2,
#     "Gold 1Kg": 0.05,
#     "Silver 1Kg": 0.05,
#     "Ham_Petrol_Fiyati 1L": 0.9,
#     "Elektrik_Ucreti 1kW": 2.5,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 1,
#     "EUR": 1
# }
# printer_materials = {
#     "Aluminum 1Kg": 0.2,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 0.4,
#     "Elektrik_Ucreti 1kW": 1.5,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 0.9,
#     "EUR": 1
# }
# camera_materials = {
#     "Aluminum 1Kg": 0.3,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0.02,
#     "Silver 1Kg": 0.05,
#     "Ham_Petrol_Fiyati 1L": 0.6,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.02,
#     "USD": 1,
#     "EUR": 1
# }
# electricKettle_materials = {
#     "Aluminum 1Kg": 0.15,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 0.7,
#     "Elektrik_Ucreti 1kW": 0.8,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.01,
#     "USD": 0.9,
#     "EUR": 1
# }
# blender_materials = {
#     "Aluminum 1Kg": 0.2,
#     "Copper 1Kg": 0.1,
#     "Gold 1Kg": 0,
#     "Silver 1Kg": 0.02,
#     "Ham_Petrol_Fiyati 1L": 0.5,
#     "Elektrik_Ucreti 1kW": 1,
#     "Asgari_Ucret 1 iş günü": 0,
#     "Dogal_Gaz 100m^3": 0.015,
#     "USD": 0.8,
#     "EUR": 1
# }
#
# insert_daily_costs("CopperCable 1m", copperCable_materials)
# insert_daily_costs("GoldCable 1m", GoldCable_materials)
# insert_daily_costs("USBCable", USBCable_materials)
# insert_daily_costs("SilverCable 1m", silverCable_materials)
# insert_daily_costs("Toy_Car", toy_Car_materials)
# insert_daily_costs("Toy_AliminumGun", toy_AliminumGun_materials)
# insert_daily_costs("Toy_TeddyBear", toy_TeddyBear_materials)
# insert_daily_costs("GamePad", gamePad_materials)
# insert_daily_costs("Laptop", laptop_materials)
# insert_daily_costs("Smartphone", smartphone_materials)
# insert_daily_costs("Tablet", tablet_materials)
# insert_daily_costs("Smart Watch", smartwatch_materials)
# insert_daily_costs("Gaming Mouse", gamingMouse_materials)
# insert_daily_costs("Electric Fan", electricFan_materials)
# insert_daily_costs("Microwave", microwave_materials)
# insert_daily_costs("Vacuum Cleaner", vacuumCleaner_materials)
# insert_daily_costs("Air Conditioner", airConditioner_materials)
# insert_daily_costs("Television", television_materials)
# insert_daily_costs("Refrigerator", refrigerator_materials)
# insert_daily_costs("Printer", printer_materials)
# insert_daily_costs("Camera", camera_materials)
# insert_daily_costs("Electric Kettle", electricKettle_materials)
# insert_daily_costs("Blender", blender_materials)


# product_materials_1 = {'Aluminum 1Kg': 0.15, 'Copper 1Kg': 0, 'Gold 1Kg': 0.154, 'Silver 1Kg': 0.289, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.306, 'EUR': 0}
# insert_daily_costs("Product 1", product_materials_1)
#
# product_materials_2 = {'Aluminum 1Kg': 0.49, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.1, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.043, 'USD': 0.007, 'EUR': 0}
# insert_daily_costs("Product 2", product_materials_2)
#
# product_materials_3 = {'Aluminum 1Kg': 0.08, 'Copper 1Kg': 0, 'Gold 1Kg': 0.055, 'Silver 1Kg': 0.044, 'Ham_Petrol_Fiyati 1L': 0.485, 'Elektrik_Ucreti 1kW': 0.276, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.022, 'EUR': 0.423}
# insert_daily_costs("Product 3", product_materials_3)
#
# product_materials_4 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.044, 'Gold 1Kg': 0.093, 'Silver 1Kg': 0.361, 'Ham_Petrol_Fiyati 1L': 0.069, 'Elektrik_Ucreti 1kW': 0.071, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.44, 'USD': 0, 'EUR': 0.021}
# insert_daily_costs("Product 4", product_materials_4)
#
# product_materials_5 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.491, 'Silver 1Kg': 0.226, 'Ham_Petrol_Fiyati 1L': 0.304, 'Elektrik_Ucreti 1kW': 0.412, 'Asgari_Ucret 1 iş günü': 0.118, 'Dogal_Gaz 100m^3': 0, 'USD': 0.296, 'EUR': 0}
# insert_daily_costs("Product 5", product_materials_5)
#
# product_materials_6 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.035, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.389, 'EUR': 0.48}
# insert_daily_costs("Product 6", product_materials_6)
#
# product_materials_7 = {'Aluminum 1Kg': 0.428, 'Copper 1Kg': 0.119, 'Gold 1Kg': 0.381, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.265, 'USD': 0, 'EUR': 0.233}
# insert_daily_costs("Product 7", product_materials_7)
#
# product_materials_8 = {'Aluminum 1Kg': 0.229, 'Copper 1Kg': 0.051, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.245, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.489, 'Dogal_Gaz 100m^3': 0.398, 'USD': 0.43, 'EUR': 0.176}
# insert_daily_costs("Product 8", product_materials_8)
#
# product_materials_9 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.341, 'Gold 1Kg': 0.008, 'Silver 1Kg': 0.416, 'Ham_Petrol_Fiyati 1L': 0.409, 'Elektrik_Ucreti 1kW': 0.144, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.083, 'EUR': 0.402}
# insert_daily_costs("Product 9", product_materials_9)
#
# product_materials_10 = {'Aluminum 1Kg': 0.392, 'Copper 1Kg': 0, 'Gold 1Kg': 0.15, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.362, 'USD': 0.284, 'EUR': 0.256}
# insert_daily_costs("Product 10", product_materials_10)
#
# product_materials_11 = {'Aluminum 1Kg': 0.485, 'Copper 1Kg': 0, 'Gold 1Kg': 0.137, 'Silver 1Kg': 0.178, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.466, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 11", product_materials_11)
#
# product_materials_12 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.019, 'Gold 1Kg': 0, 'Silver 1Kg': 0.117, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.29, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.217, 'EUR': 0}
# insert_daily_costs("Product 12", product_materials_12)
#
# product_materials_13 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.124, 'Dogal_Gaz 100m^3': 0.384, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 13", product_materials_13)
#
# product_materials_14 = {'Aluminum 1Kg': 0.215, 'Copper 1Kg': 0.032, 'Gold 1Kg': 0, 'Silver 1Kg': 0.006, 'Ham_Petrol_Fiyati 1L': 0.496, 'Elektrik_Ucreti 1kW': 0.395, 'Asgari_Ucret 1 iş günü': 0.29, 'Dogal_Gaz 100m^3': 0.054, 'USD': 0.319, 'EUR': 0.038}
# insert_daily_costs("Product 14", product_materials_14)
#
# product_materials_15 = {'Aluminum 1Kg': 0.419, 'Copper 1Kg': 0.317, 'Gold 1Kg': 0, 'Silver 1Kg': 0.17, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.429}
# insert_daily_costs("Product 15", product_materials_15)
#
# product_materials_16 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.482, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.458, 'Asgari_Ucret 1 iş günü': 0.252, 'Dogal_Gaz 100m^3': 0.491, 'USD': 0.453, 'EUR': 0}
# insert_daily_costs("Product 16", product_materials_16)
#
# product_materials_17 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.163, 'Gold 1Kg': 0, 'Silver 1Kg': 0.362, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.226, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.268, 'USD': 0, 'EUR': 0.263}
# insert_daily_costs("Product 17", product_materials_17)
#
# product_materials_18 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.224, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.028, 'Elektrik_Ucreti 1kW': 0.248, 'Asgari_Ucret 1 iş günü': 0.181, 'Dogal_Gaz 100m^3': 0.335, 'USD': 0, 'EUR': 0.482}
# insert_daily_costs("Product 18", product_materials_18)
#
# product_materials_19 = {'Aluminum 1Kg': 0.379, 'Copper 1Kg': 0.005, 'Gold 1Kg': 0, 'Silver 1Kg': 0.284, 'Ham_Petrol_Fiyati 1L': 0.066, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.416, 'Dogal_Gaz 100m^3': 0.039, 'USD': 0, 'EUR': 0.139}
# insert_daily_costs("Product 19", product_materials_19)
#
# product_materials_20 = {'Aluminum 1Kg': 0.328, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.176, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.184, 'EUR': 0}
# insert_daily_costs("Product 20", product_materials_20)
#
# product_materials_21 = {'Aluminum 1Kg': 0.061, 'Copper 1Kg': 0.308, 'Gold 1Kg': 0, 'Silver 1Kg': 0.256, 'Ham_Petrol_Fiyati 1L': 0.154, 'Elektrik_Ucreti 1kW': 0.272, 'Asgari_Ucret 1 iş günü': 0.06, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 21", product_materials_21)
#
# product_materials_22 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.005, 'Gold 1Kg': 0, 'Silver 1Kg': 0.382, 'Ham_Petrol_Fiyati 1L': 0.481, 'Elektrik_Ucreti 1kW': 0.164, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.466, 'USD': 0, 'EUR': 0.134}
# insert_daily_costs("Product 22", product_materials_22)
#
# product_materials_23 = {'Aluminum 1Kg': 0.093, 'Copper 1Kg': 0.062, 'Gold 1Kg': 0.39, 'Silver 1Kg': 0.353, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.201, 'Dogal_Gaz 100m^3': 0, 'USD': 0.253, 'EUR': 0.41}
# insert_daily_costs("Product 23", product_materials_23)
#
# product_materials_24 = {'Aluminum 1Kg': 0.282, 'Copper 1Kg': 0, 'Gold 1Kg': 0.016, 'Silver 1Kg': 0.372, 'Ham_Petrol_Fiyati 1L': 0.457, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.103, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 24", product_materials_24)
#
# product_materials_25 = {'Aluminum 1Kg': 0.39, 'Copper 1Kg': 0.053, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.447, 'USD': 0, 'EUR': 0.451}
# insert_daily_costs("Product 25", product_materials_25)
#
# product_materials_26 = {'Aluminum 1Kg': 0.376, 'Copper 1Kg': 0.104, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.402, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.032, 'Dogal_Gaz 100m^3': 0.321, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 26", product_materials_26)
#
# product_materials_27 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.26, 'Gold 1Kg': 0.113, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.208, 'Dogal_Gaz 100m^3': 0, 'USD': 0.311, 'EUR': 0}
# insert_daily_costs("Product 27", product_materials_27)
#
# product_materials_28 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.458, 'Gold 1Kg': 0, 'Silver 1Kg': 0.271, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.334, 'Asgari_Ucret 1 iş günü': 0.251, 'Dogal_Gaz 100m^3': 0.487, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 28", product_materials_28)
#
# product_materials_29 = {'Aluminum 1Kg': 0.409, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.082, 'Dogal_Gaz 100m^3': 0.052, 'USD': 0.015, 'EUR': 0.336}
# insert_daily_costs("Product 29", product_materials_29)
#
# product_materials_30 = {'Aluminum 1Kg': 0.136, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.362, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.072, 'Dogal_Gaz 100m^3': 0.038, 'USD': 0.262, 'EUR': 0}
# insert_daily_costs("Product 30", product_materials_30)
#
# product_materials_31 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.445, 'EUR': 0}
# insert_daily_costs("Product 31", product_materials_31)
#
# product_materials_32 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.385, 'Gold 1Kg': 0, 'Silver 1Kg': 0.397, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.334, 'Dogal_Gaz 100m^3': 0.483, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 32", product_materials_32)
#
# product_materials_33 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.233, 'Dogal_Gaz 100m^3': 0, 'USD': 0.424, 'EUR': 0}
# insert_daily_costs("Product 33", product_materials_33)
#
# product_materials_34 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.239, 'Asgari_Ucret 1 iş günü': 0.3, 'Dogal_Gaz 100m^3': 0, 'USD': 0.047, 'EUR': 0}
# insert_daily_costs("Product 34", product_materials_34)
#
# product_materials_35 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.203, 'Silver 1Kg': 0.137, 'Ham_Petrol_Fiyati 1L': 0.388, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.242, 'EUR': 0}
# insert_daily_costs("Product 35", product_materials_35)
#
# product_materials_36 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.007, 'Gold 1Kg': 0.49, 'Silver 1Kg': 0.028, 'Ham_Petrol_Fiyati 1L': 0.142, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.049, 'USD': 0.017, 'EUR': 0.161}
# insert_daily_costs("Product 36", product_materials_36)
#
# product_materials_37 = {'Aluminum 1Kg': 0.296, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.007, 'Ham_Petrol_Fiyati 1L': 0.259, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.049, 'Dogal_Gaz 100m^3': 0.405, 'USD': 0, 'EUR': 0.405}
# insert_daily_costs("Product 37", product_materials_37)
#
# product_materials_38 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.331, 'Gold 1Kg': 0.238, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.287, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.257, 'EUR': 0}
# insert_daily_costs("Product 38", product_materials_38)
#
# product_materials_39 = {'Aluminum 1Kg': 0.14, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.447, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 39", product_materials_39)
#
# product_materials_40 = {'Aluminum 1Kg': 0.2, 'Copper 1Kg': 0.291, 'Gold 1Kg': 0.412, 'Silver 1Kg': 0.398, 'Ham_Petrol_Fiyati 1L': 0.46, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.322, 'USD': 0, 'EUR': 0.109}
# insert_daily_costs("Product 40", product_materials_40)
#
# product_materials_41 = {'Aluminum 1Kg': 0.35, 'Copper 1Kg': 0.234, 'Gold 1Kg': 0.151, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.293}
# insert_daily_costs("Product 41", product_materials_41)
#
# product_materials_42 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.244, 'Gold 1Kg': 0.262, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.021, 'Elektrik_Ucreti 1kW': 0.068, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.336, 'USD': 0.188, 'EUR': 0}
# insert_daily_costs("Product 42", product_materials_42)
#
# product_materials_43 = {'Aluminum 1Kg': 0.253, 'Copper 1Kg': 0.409, 'Gold 1Kg': 0.322, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.472, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.409, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 43", product_materials_43)
#
# product_materials_44 = {'Aluminum 1Kg': 0.408, 'Copper 1Kg': 0.474, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.2, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.229, 'EUR': 0}
# insert_daily_costs("Product 44", product_materials_44)
#
# product_materials_45 = {'Aluminum 1Kg': 0.37, 'Copper 1Kg': 0.05, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.216, 'USD': 0.207, 'EUR': 0}
# insert_daily_costs("Product 45", product_materials_45)
#
# product_materials_46 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.191, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.303, 'Elektrik_Ucreti 1kW': 0.25, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.305}
# insert_daily_costs("Product 46", product_materials_46)
#
# product_materials_47 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.342, 'Silver 1Kg': 0.468, 'Ham_Petrol_Fiyati 1L': 0.18, 'Elektrik_Ucreti 1kW': 0.063, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 47", product_materials_47)
#
# product_materials_48 = {'Aluminum 1Kg': 0.367, 'Copper 1Kg': 0.296, 'Gold 1Kg': 0.11, 'Silver 1Kg': 0.294, 'Ham_Petrol_Fiyati 1L': 0.222, 'Elektrik_Ucreti 1kW': 0.496, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.37, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 48", product_materials_48)
#
# product_materials_49 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.183, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.161, 'EUR': 0}
# insert_daily_costs("Product 49", product_materials_49)
#
# product_materials_50 = {'Aluminum 1Kg': 0.113, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.047, 'Ham_Petrol_Fiyati 1L': 0.172, 'Elektrik_Ucreti 1kW': 0.239, 'Asgari_Ucret 1 iş günü': 0.481, 'Dogal_Gaz 100m^3': 0.327, 'USD': 0, 'EUR': 0.168}
# insert_daily_costs("Product 50", product_materials_50)
#
# product_materials_51 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.008, 'USD': 0.428, 'EUR': 0}
# insert_daily_costs("Product 51", product_materials_51)
#
# product_materials_52 = {'Aluminum 1Kg': 0.047, 'Copper 1Kg': 0, 'Gold 1Kg': 0.209, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.13, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.324}
# insert_daily_costs("Product 52", product_materials_52)
#
# product_materials_53 = {'Aluminum 1Kg': 0.039, 'Copper 1Kg': 0.21, 'Gold 1Kg': 0, 'Silver 1Kg': 0.069, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.495, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.484, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 53", product_materials_53)
#
# product_materials_54 = {'Aluminum 1Kg': 0.096, 'Copper 1Kg': 0, 'Gold 1Kg': 0.179, 'Silver 1Kg': 0.447, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.009, 'EUR': 0}
# insert_daily_costs("Product 54", product_materials_54)
#
# product_materials_55 = {'Aluminum 1Kg': 0.435, 'Copper 1Kg': 0.216, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.4, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.09, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 55", product_materials_55)
#
# product_materials_56 = {'Aluminum 1Kg': 0.151, 'Copper 1Kg': 0.479, 'Gold 1Kg': 0.442, 'Silver 1Kg': 0.407, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.394, 'Dogal_Gaz 100m^3': 0.442, 'USD': 0, 'EUR': 0.448}
# insert_daily_costs("Product 56", product_materials_56)
#
# product_materials_57 = {'Aluminum 1Kg': 0.068, 'Copper 1Kg': 0.497, 'Gold 1Kg': 0.385, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.257, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.245, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 57", product_materials_57)
#
# product_materials_58 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.047, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.359, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.154, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 58", product_materials_58)
#
# product_materials_59 = {'Aluminum 1Kg': 0.09, 'Copper 1Kg': 0, 'Gold 1Kg': 0.453, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.28, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.188, 'USD': 0.045, 'EUR': 0}
# insert_daily_costs("Product 59", product_materials_59)
#
# product_materials_60 = {'Aluminum 1Kg': 0.204, 'Copper 1Kg': 0.471, 'Gold 1Kg': 0.293, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.235, 'Dogal_Gaz 100m^3': 0.212, 'USD': 0.052, 'EUR': 0}
# insert_daily_costs("Product 60", product_materials_60)
#
# product_materials_61 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.078, 'Silver 1Kg': 0.415, 'Ham_Petrol_Fiyati 1L': 0.348, 'Elektrik_Ucreti 1kW': 0.439, 'Asgari_Ucret 1 iş günü': 0.2, 'Dogal_Gaz 100m^3': 0, 'USD': 0.416, 'EUR': 0}
# insert_daily_costs("Product 61", product_materials_61)
#
# product_materials_62 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.366, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.099, 'Elektrik_Ucreti 1kW': 0.45, 'Asgari_Ucret 1 iş günü': 0.441, 'Dogal_Gaz 100m^3': 0, 'USD': 0.054, 'EUR': 0}
# insert_daily_costs("Product 62", product_materials_62)
#
# product_materials_63 = {'Aluminum 1Kg': 0.294, 'Copper 1Kg': 0.308, 'Gold 1Kg': 0.24, 'Silver 1Kg': 0.457, 'Ham_Petrol_Fiyati 1L': 0.148, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.021, 'Dogal_Gaz 100m^3': 0.438, 'USD': 0, 'EUR': 0.172}
# insert_daily_costs("Product 63", product_materials_63)
#
# product_materials_64 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.222, 'Gold 1Kg': 0.148, 'Silver 1Kg': 0.428, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.053, 'Asgari_Ucret 1 iş günü': 0.042, 'Dogal_Gaz 100m^3': 0, 'USD': 0.355, 'EUR': 0}
# insert_daily_costs("Product 64", product_materials_64)
#
# product_materials_65 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.167, 'EUR': 0}
# insert_daily_costs("Product 65", product_materials_65)
#
# product_materials_66 = {'Aluminum 1Kg': 0.5, 'Copper 1Kg': 0.47, 'Gold 1Kg': 0.036, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.051, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.173, 'Dogal_Gaz 100m^3': 0.194, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 66", product_materials_66)
#
# product_materials_67 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.163, 'Gold 1Kg': 0, 'Silver 1Kg': 0.301, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.019, 'Dogal_Gaz 100m^3': 0.025, 'USD': 0.024, 'EUR': 0.363}
# insert_daily_costs("Product 67", product_materials_67)
#
# product_materials_68 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.135, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.338, 'Elektrik_Ucreti 1kW': 0.011, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.04, 'EUR': 0.183}
# insert_daily_costs("Product 68", product_materials_68)
#
# product_materials_69 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.183, 'Dogal_Gaz 100m^3': 0.372, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 69", product_materials_69)
#
# product_materials_70 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.204, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.336, 'Elektrik_Ucreti 1kW': 0.294, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.39, 'EUR': 0}
# insert_daily_costs("Product 70", product_materials_70)
#
# product_materials_71 = {'Aluminum 1Kg': 0.008, 'Copper 1Kg': 0, 'Gold 1Kg': 0.232, 'Silver 1Kg': 0.082, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.008, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.228}
# insert_daily_costs("Product 71", product_materials_71)
#
# product_materials_72 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.162, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.242, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.221, 'USD': 0.084, 'EUR': 0}
# insert_daily_costs("Product 72", product_materials_72)
#
# product_materials_73 = {'Aluminum 1Kg': 0.315, 'Copper 1Kg': 0.245, 'Gold 1Kg': 0, 'Silver 1Kg': 0.063, 'Ham_Petrol_Fiyati 1L': 0.242, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.466, 'Dogal_Gaz 100m^3': 0.108, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 73", product_materials_73)
#
# product_materials_74 = {'Aluminum 1Kg': 0.229, 'Copper 1Kg': 0.391, 'Gold 1Kg': 0, 'Silver 1Kg': 0.47, 'Ham_Petrol_Fiyati 1L': 0.138, 'Elektrik_Ucreti 1kW': 0.17, 'Asgari_Ucret 1 iş günü': 0.37, 'Dogal_Gaz 100m^3': 0, 'USD': 0.379, 'EUR': 0.232}
# insert_daily_costs("Product 74", product_materials_74)
#
# product_materials_75 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.104, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.178, 'Elektrik_Ucreti 1kW': 0.441, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.08, 'USD': 0.08, 'EUR': 0.333}
# insert_daily_costs("Product 75", product_materials_75)
#
# product_materials_76 = {'Aluminum 1Kg': 0.411, 'Copper 1Kg': 0, 'Gold 1Kg': 0.251, 'Silver 1Kg': 0.461, 'Ham_Petrol_Fiyati 1L': 0.353, 'Elektrik_Ucreti 1kW': 0.395, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.16, 'EUR': 0}
# insert_daily_costs("Product 76", product_materials_76)
#
# product_materials_77 = {'Aluminum 1Kg': 0.4, 'Copper 1Kg': 0, 'Gold 1Kg': 0.204, 'Silver 1Kg': 0.075, 'Ham_Petrol_Fiyati 1L': 0.206, 'Elektrik_Ucreti 1kW': 0.427, 'Asgari_Ucret 1 iş günü': 0.481, 'Dogal_Gaz 100m^3': 0.085, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 77", product_materials_77)
#
# product_materials_78 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.132, 'Silver 1Kg': 0.427, 'Ham_Petrol_Fiyati 1L': 0.085, 'Elektrik_Ucreti 1kW': 0.018, 'Asgari_Ucret 1 iş günü': 0.057, 'Dogal_Gaz 100m^3': 0.057, 'USD': 0.305, 'EUR': 0}
# insert_daily_costs("Product 78", product_materials_78)
#
# product_materials_79 = {'Aluminum 1Kg': 0.208, 'Copper 1Kg': 0, 'Gold 1Kg': 0.145, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.263, 'Elektrik_Ucreti 1kW': 0.406, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.431, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 79", product_materials_79)
#
# product_materials_80 = {'Aluminum 1Kg': 0.314, 'Copper 1Kg': 0.481, 'Gold 1Kg': 0.226, 'Silver 1Kg': 0.195, 'Ham_Petrol_Fiyati 1L': 0.458, 'Elektrik_Ucreti 1kW': 0.183, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.463}
# insert_daily_costs("Product 80", product_materials_80)
#
# product_materials_81 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.15, 'USD': 0, 'EUR': 0.187}
# insert_daily_costs("Product 81", product_materials_81)
#
# product_materials_82 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.218, 'Gold 1Kg': 0.029, 'Silver 1Kg': 0.328, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.013, 'Dogal_Gaz 100m^3': 0, 'USD': 0.015, 'EUR': 0.437}
# insert_daily_costs("Product 82", product_materials_82)
#
# product_materials_83 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.178, 'Silver 1Kg': 0.252, 'Ham_Petrol_Fiyati 1L': 0.46, 'Elektrik_Ucreti 1kW': 0.431, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.303, 'USD': 0.176, 'EUR': 0}
# insert_daily_costs("Product 83", product_materials_83)
#
# product_materials_84 = {'Aluminum 1Kg': 0.451, 'Copper 1Kg': 0.138, 'Gold 1Kg': 0.373, 'Silver 1Kg': 0.152, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.105, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.117, 'EUR': 0.423}
# insert_daily_costs("Product 84", product_materials_84)
#
# product_materials_85 = {'Aluminum 1Kg': 0.179, 'Copper 1Kg': 0.092, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.263, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.093}
# insert_daily_costs("Product 85", product_materials_85)
#
# product_materials_86 = {'Aluminum 1Kg': 0.395, 'Copper 1Kg': 0.242, 'Gold 1Kg': 0.016, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.043, 'Elektrik_Ucreti 1kW': 0.477, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.237, 'EUR': 0.012}
# insert_daily_costs("Product 86", product_materials_86)
#
# product_materials_87 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.144, 'Gold 1Kg': 0.037, 'Silver 1Kg': 0.113, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.004, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.379}
# insert_daily_costs("Product 87", product_materials_87)
#
# product_materials_88 = {'Aluminum 1Kg': 0.366, 'Copper 1Kg': 0.456, 'Gold 1Kg': 0.089, 'Silver 1Kg': 0.266, 'Ham_Petrol_Fiyati 1L': 0.034, 'Elektrik_Ucreti 1kW': 0.267, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.347}
# insert_daily_costs("Product 88", product_materials_88)
#
# product_materials_89 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.205, 'Gold 1Kg': 0.267, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.16, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 89", product_materials_89)
#
# product_materials_90 = {'Aluminum 1Kg': 0.364, 'Copper 1Kg': 0.099, 'Gold 1Kg': 0, 'Silver 1Kg': 0.48, 'Ham_Petrol_Fiyati 1L': 0.47, 'Elektrik_Ucreti 1kW': 0.235, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.244, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 90", product_materials_90)
#
# product_materials_91 = {'Aluminum 1Kg': 0.428, 'Copper 1Kg': 0.113, 'Gold 1Kg': 0, 'Silver 1Kg': 0.5, 'Ham_Petrol_Fiyati 1L': 0.204, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.21, 'Dogal_Gaz 100m^3': 0, 'USD': 0.077, 'EUR': 0.458}
# insert_daily_costs("Product 91", product_materials_91)
#
# product_materials_92 = {'Aluminum 1Kg': 0.246, 'Copper 1Kg': 0.275, 'Gold 1Kg': 0, 'Silver 1Kg': 0.35, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.016, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 92", product_materials_92)
#
# product_materials_93 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.484, 'Ham_Petrol_Fiyati 1L': 0.067, 'Elektrik_Ucreti 1kW': 0.228, 'Asgari_Ucret 1 iş günü': 0.005, 'Dogal_Gaz 100m^3': 0, 'USD': 0.457, 'EUR': 0}
# insert_daily_costs("Product 93", product_materials_93)
#
# product_materials_94 = {'Aluminum 1Kg': 0.415, 'Copper 1Kg': 0, 'Gold 1Kg': 0.204, 'Silver 1Kg': 0.423, 'Ham_Petrol_Fiyati 1L': 0.438, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.04, 'USD': 0, 'EUR': 0.205}
# insert_daily_costs("Product 94", product_materials_94)
#
# product_materials_95 = {'Aluminum 1Kg': 0.01, 'Copper 1Kg': 0.122, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.161, 'Dogal_Gaz 100m^3': 0.038, 'USD': 0.344, 'EUR': 0.35}
# insert_daily_costs("Product 95", product_materials_95)
#
# product_materials_96 = {'Aluminum 1Kg': 0.353, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.172, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.148, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.236, 'USD': 0.314, 'EUR': 0}
# insert_daily_costs("Product 96", product_materials_96)
#
# product_materials_97 = {'Aluminum 1Kg': 0.305, 'Copper 1Kg': 0, 'Gold 1Kg': 0.268, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.257, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.373}
# insert_daily_costs("Product 97", product_materials_97)
#
# product_materials_98 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.349, 'Gold 1Kg': 0.03, 'Silver 1Kg': 0.295, 'Ham_Petrol_Fiyati 1L': 0.141, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.071}
# insert_daily_costs("Product 98", product_materials_98)
#
# product_materials_99 = {'Aluminum 1Kg': 0.408, 'Copper 1Kg': 0.155, 'Gold 1Kg': 0.162, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.351, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.154, 'EUR': 0.341}
# insert_daily_costs("Product 99", product_materials_99)
#
# product_materials_100 = {'Aluminum 1Kg': 0.346, 'Copper 1Kg': 0.011, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.037, 'USD': 0.091, 'EUR': 0.1}
# insert_daily_costs("Product 100", product_materials_100)
#
# product_materials_101 = {'Aluminum 1Kg': 0.202, 'Copper 1Kg': 0, 'Gold 1Kg': 0.032, 'Silver 1Kg': 0.443, 'Ham_Petrol_Fiyati 1L': 0.19, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.396, 'Dogal_Gaz 100m^3': 0.086, 'USD': 0.141, 'EUR': 0.165}
# insert_daily_costs("Product 101", product_materials_101)
#
# product_materials_102 = {'Aluminum 1Kg': 0.479, 'Copper 1Kg': 0.186, 'Gold 1Kg': 0.265, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.315, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.095, 'EUR': 0.288}
# insert_daily_costs("Product 102", product_materials_102)
#
# product_materials_103 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.216, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.205, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.11, 'Dogal_Gaz 100m^3': 0.428, 'USD': 0, 'EUR': 0.025}
# insert_daily_costs("Product 103", product_materials_103)
#
# product_materials_104 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.184, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.279, 'USD': 0.24, 'EUR': 0.187}
# insert_daily_costs("Product 104", product_materials_104)
#
# product_materials_105 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.46, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.417, 'Elektrik_Ucreti 1kW': 0.338, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.429, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 105", product_materials_105)
#
# product_materials_106 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.201, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.251, 'Dogal_Gaz 100m^3': 0, 'USD': 0.171, 'EUR': 0}
# insert_daily_costs("Product 106", product_materials_106)
#
# product_materials_107 = {'Aluminum 1Kg': 0.348, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.43, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.118, 'Asgari_Ucret 1 iş günü': 0.067, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 107", product_materials_107)
#
# product_materials_108 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.144, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.334, 'EUR': 0}
# insert_daily_costs("Product 108", product_materials_108)
#
# product_materials_109 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.428, 'Silver 1Kg': 0.233, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.274, 'Dogal_Gaz 100m^3': 0.126, 'USD': 0, 'EUR': 0.311}
# insert_daily_costs("Product 109", product_materials_109)
#
# product_materials_110 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.311, 'Ham_Petrol_Fiyati 1L': 0.468, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.428, 'Dogal_Gaz 100m^3': 0.051, 'USD': 0.443, 'EUR': 0.45}
# insert_daily_costs("Product 110", product_materials_110)
#
# product_materials_111 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.431, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.499, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.337, 'USD': 0.024, 'EUR': 0.213}
# insert_daily_costs("Product 111", product_materials_111)
#
# product_materials_112 = {'Aluminum 1Kg': 0.33, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.358, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.004, 'Dogal_Gaz 100m^3': 0.052, 'USD': 0, 'EUR': 0.268}
# insert_daily_costs("Product 112", product_materials_112)
#
# product_materials_113 = {'Aluminum 1Kg': 0.372, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.355, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.14, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 113", product_materials_113)
#
# product_materials_114 = {'Aluminum 1Kg': 0.099, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.004, 'Dogal_Gaz 100m^3': 0.041, 'USD': 0.445, 'EUR': 0.378}
# insert_daily_costs("Product 114", product_materials_114)
#
# product_materials_115 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.26, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.245, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.396, 'USD': 0.048, 'EUR': 0}
# insert_daily_costs("Product 115", product_materials_115)
#
# product_materials_116 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.323, 'Gold 1Kg': 0.292, 'Silver 1Kg': 0.085, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.186, 'USD': 0.354, 'EUR': 0.202}
# insert_daily_costs("Product 116", product_materials_116)
#
# product_materials_117 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.065, 'Gold 1Kg': 0, 'Silver 1Kg': 0.267, 'Ham_Petrol_Fiyati 1L': 0.436, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.417, 'Dogal_Gaz 100m^3': 0, 'USD': 0.496, 'EUR': 0}
# insert_daily_costs("Product 117", product_materials_117)
#
# product_materials_118 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.008, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.238, 'Elektrik_Ucreti 1kW': 0.037, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.338, 'USD': 0.481, 'EUR': 0}
# insert_daily_costs("Product 118", product_materials_118)
#
# product_materials_119 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.249, 'Ham_Petrol_Fiyati 1L': 0.466, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.26, 'Dogal_Gaz 100m^3': 0.343, 'USD': 0.051, 'EUR': 0.478}
# insert_daily_costs("Product 119", product_materials_119)
#
# product_materials_120 = {'Aluminum 1Kg': 0.005, 'Copper 1Kg': 0.058, 'Gold 1Kg': 0.178, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.448, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 120", product_materials_120)
#
# product_materials_121 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.39, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 121", product_materials_121)
#
# product_materials_122 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.188, 'Silver 1Kg': 0.247, 'Ham_Petrol_Fiyati 1L': 0.229, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.228, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 122", product_materials_122)
#
# product_materials_123 = {'Aluminum 1Kg': 0.427, 'Copper 1Kg': 0, 'Gold 1Kg': 0.293, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.062, 'Elektrik_Ucreti 1kW': 0.233, 'Asgari_Ucret 1 iş günü': 0.271, 'Dogal_Gaz 100m^3': 0.11, 'USD': 0.207, 'EUR': 0.332}
# insert_daily_costs("Product 123", product_materials_123)
#
# product_materials_124 = {'Aluminum 1Kg': 0.125, 'Copper 1Kg': 0, 'Gold 1Kg': 0.45, 'Silver 1Kg': 0.038, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.415}
# insert_daily_costs("Product 124", product_materials_124)
#
# product_materials_125 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.357, 'Gold 1Kg': 0.199, 'Silver 1Kg': 0.207, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.412, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 125", product_materials_125)
#
# product_materials_126 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.277, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.431, 'Elektrik_Ucreti 1kW': 0.436, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 126", product_materials_126)
#
# product_materials_127 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.008, 'Gold 1Kg': 0, 'Silver 1Kg': 0.354, 'Ham_Petrol_Fiyati 1L': 0.132, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.281, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 127", product_materials_127)
#
# product_materials_128 = {'Aluminum 1Kg': 0.218, 'Copper 1Kg': 0.014, 'Gold 1Kg': 0.182, 'Silver 1Kg': 0.083, 'Ham_Petrol_Fiyati 1L': 0.292, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.44, 'USD': 0, 'EUR': 0.457}
# insert_daily_costs("Product 128", product_materials_128)
#
# product_materials_129 = {'Aluminum 1Kg': 0.112, 'Copper 1Kg': 0.319, 'Gold 1Kg': 0.003, 'Silver 1Kg': 0.411, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.425, 'EUR': 0}
# insert_daily_costs("Product 129", product_materials_129)
#
# product_materials_130 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.49, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.381, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.128, 'EUR': 0.125}
# insert_daily_costs("Product 130", product_materials_130)
#
# product_materials_131 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.122, 'Gold 1Kg': 0, 'Silver 1Kg': 0.373, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.106, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 131", product_materials_131)
#
# product_materials_132 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.447, 'Gold 1Kg': 0.145, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.204, 'Asgari_Ucret 1 iş günü': 0.151, 'Dogal_Gaz 100m^3': 0, 'USD': 0.199, 'EUR': 0}
# insert_daily_costs("Product 132", product_materials_132)
#
# product_materials_133 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.2, 'Silver 1Kg': 0.457, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.407, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.103, 'USD': 0.431, 'EUR': 0}
# insert_daily_costs("Product 133", product_materials_133)
#
# product_materials_134 = {'Aluminum 1Kg': 0.231, 'Copper 1Kg': 0.32, 'Gold 1Kg': 0, 'Silver 1Kg': 0.051, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.313, 'Dogal_Gaz 100m^3': 0, 'USD': 0.174, 'EUR': 0.37}
# insert_daily_costs("Product 134", product_materials_134)
#
# product_materials_135 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.348, 'Silver 1Kg': 0.433, 'Ham_Petrol_Fiyati 1L': 0.296, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 135", product_materials_135)
#
# product_materials_136 = {'Aluminum 1Kg': 0.033, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.148, 'Asgari_Ucret 1 iş günü': 0.05, 'Dogal_Gaz 100m^3': 0, 'USD': 0.233, 'EUR': 0.223}
# insert_daily_costs("Product 136", product_materials_136)
#
# product_materials_137 = {'Aluminum 1Kg': 0.419, 'Copper 1Kg': 0, 'Gold 1Kg': 0.105, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.422, 'Dogal_Gaz 100m^3': 0, 'USD': 0.176, 'EUR': 0}
# insert_daily_costs("Product 137", product_materials_137)
#
# product_materials_138 = {'Aluminum 1Kg': 0.496, 'Copper 1Kg': 0.274, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.287, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.234}
# insert_daily_costs("Product 138", product_materials_138)
#
# product_materials_139 = {'Aluminum 1Kg': 0.214, 'Copper 1Kg': 0.062, 'Gold 1Kg': 0, 'Silver 1Kg': 0.372, 'Ham_Petrol_Fiyati 1L': 0.424, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.436, 'Dogal_Gaz 100m^3': 0.32, 'USD': 0.208, 'EUR': 0}
# insert_daily_costs("Product 139", product_materials_139)
#
# product_materials_140 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.081, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.383, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.131, 'EUR': 0}
# insert_daily_costs("Product 140", product_materials_140)
#
# product_materials_141 = {'Aluminum 1Kg': 0.219, 'Copper 1Kg': 0.155, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.185, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 141", product_materials_141)
#
# product_materials_142 = {'Aluminum 1Kg': 0.038, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.091, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.354, 'Dogal_Gaz 100m^3': 0.086, 'USD': 0.381, 'EUR': 0}
# insert_daily_costs("Product 142", product_materials_142)
#
# product_materials_143 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.473, 'Gold 1Kg': 0.394, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.253, 'Elektrik_Ucreti 1kW': 0.116, 'Asgari_Ucret 1 iş günü': 0.446, 'Dogal_Gaz 100m^3': 0.47, 'USD': 0.018, 'EUR': 0.399}
# insert_daily_costs("Product 143", product_materials_143)
#
# product_materials_144 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.315, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.185, 'Asgari_Ucret 1 iş günü': 0.333, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 144", product_materials_144)
#
# product_materials_145 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.151, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.463, 'Elektrik_Ucreti 1kW': 0.383, 'Asgari_Ucret 1 iş günü': 0.162, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.39}
# insert_daily_costs("Product 145", product_materials_145)
#
# product_materials_146 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.405, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.06, 'Elektrik_Ucreti 1kW': 0.184, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.444}
# insert_daily_costs("Product 146", product_materials_146)
#
# product_materials_147 = {'Aluminum 1Kg': 0.22, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.008, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.227}
# insert_daily_costs("Product 147", product_materials_147)
#
# product_materials_148 = {'Aluminum 1Kg': 0.489, 'Copper 1Kg': 0, 'Gold 1Kg': 0.118, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.199, 'Elektrik_Ucreti 1kW': 0.229, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.404, 'USD': 0.376, 'EUR': 0}
# insert_daily_costs("Product 148", product_materials_148)
#
# product_materials_149 = {'Aluminum 1Kg': 0.004, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.038, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.495, 'Asgari_Ucret 1 iş günü': 0.147, 'Dogal_Gaz 100m^3': 0, 'USD': 0.209, 'EUR': 0}
# insert_daily_costs("Product 149", product_materials_149)
#
# product_materials_150 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.128, 'Gold 1Kg': 0, 'Silver 1Kg': 0.342, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.318, 'Dogal_Gaz 100m^3': 0.189, 'USD': 0.365, 'EUR': 0.032}
# insert_daily_costs("Product 150", product_materials_150)
#
# product_materials_151 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.103, 'Gold 1Kg': 0.311, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.195, 'Elektrik_Ucreti 1kW': 0.211, 'Asgari_Ucret 1 iş günü': 0.35, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 151", product_materials_151)
#
# product_materials_152 = {'Aluminum 1Kg': 0.495, 'Copper 1Kg': 0.359, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.206, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.032, 'USD': 0, 'EUR': 0.115}
# insert_daily_costs("Product 152", product_materials_152)
#
# product_materials_153 = {'Aluminum 1Kg': 0.172, 'Copper 1Kg': 0, 'Gold 1Kg': 0.366, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.397, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.185, 'Dogal_Gaz 100m^3': 0.427, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 153", product_materials_153)
#
# product_materials_154 = {'Aluminum 1Kg': 0.192, 'Copper 1Kg': 0.246, 'Gold 1Kg': 0.359, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.36, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.336, 'Dogal_Gaz 100m^3': 0.104, 'USD': 0.043, 'EUR': 0.007}
# insert_daily_costs("Product 154", product_materials_154)
#
# product_materials_155 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.46, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.247, 'USD': 0, 'EUR': 0.087}
# insert_daily_costs("Product 155", product_materials_155)
#
# product_materials_156 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.045, 'Gold 1Kg': 0.177, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.316, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.1, 'EUR': 0}
# insert_daily_costs("Product 156", product_materials_156)
#
# product_materials_157 = {'Aluminum 1Kg': 0.027, 'Copper 1Kg': 0.146, 'Gold 1Kg': 0.175, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.146, 'Dogal_Gaz 100m^3': 0, 'USD': 0.212, 'EUR': 0}
# insert_daily_costs("Product 157", product_materials_157)
#
# product_materials_158 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.122, 'Elektrik_Ucreti 1kW': 0.242, 'Asgari_Ucret 1 iş günü': 0.216, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.31}
# insert_daily_costs("Product 158", product_materials_158)
#
# product_materials_159 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.367, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.429, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.285, 'USD': 0.228, 'EUR': 0.133}
# insert_daily_costs("Product 159", product_materials_159)
#
# product_materials_160 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.127, 'Gold 1Kg': 0, 'Silver 1Kg': 0.356, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.224, 'Asgari_Ucret 1 iş günü': 0.489, 'Dogal_Gaz 100m^3': 0.005, 'USD': 0.021, 'EUR': 0.39}
# insert_daily_costs("Product 160", product_materials_160)
#
# product_materials_161 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.069, 'Gold 1Kg': 0, 'Silver 1Kg': 0.008, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.114}
# insert_daily_costs("Product 161", product_materials_161)
#
# product_materials_162 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.284, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.478, 'EUR': 0}
# insert_daily_costs("Product 162", product_materials_162)
#
# product_materials_163 = {'Aluminum 1Kg': 0.152, 'Copper 1Kg': 0, 'Gold 1Kg': 0.443, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.092, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.346}
# insert_daily_costs("Product 163", product_materials_163)
#
# product_materials_164 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.083, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.029, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 164", product_materials_164)
#
# product_materials_165 = {'Aluminum 1Kg': 0.073, 'Copper 1Kg': 0.006, 'Gold 1Kg': 0.264, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.1, 'Elektrik_Ucreti 1kW': 0.147, 'Asgari_Ucret 1 iş günü': 0.444, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 165", product_materials_165)
#
# product_materials_166 = {'Aluminum 1Kg': 0.417, 'Copper 1Kg': 0.316, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.137, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 166", product_materials_166)
#
# product_materials_167 = {'Aluminum 1Kg': 0.079, 'Copper 1Kg': 0.484, 'Gold 1Kg': 0.461, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.22, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.263}
# insert_daily_costs("Product 167", product_materials_167)
#
# product_materials_168 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.126, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 168", product_materials_168)
#
# product_materials_169 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.474, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.348, 'Dogal_Gaz 100m^3': 0.191, 'USD': 0, 'EUR': 0.141}
# insert_daily_costs("Product 169", product_materials_169)
#
# product_materials_170 = {'Aluminum 1Kg': 0.402, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.474, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 170", product_materials_170)
#
# product_materials_171 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.184, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.307, 'Elektrik_Ucreti 1kW': 0.06, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.33, 'USD': 0.447, 'EUR': 0.464}
# insert_daily_costs("Product 171", product_materials_171)
#
# product_materials_172 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.394, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.335, 'Elektrik_Ucreti 1kW': 0.48, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.156, 'USD': 0, 'EUR': 0.103}
# insert_daily_costs("Product 172", product_materials_172)
#
# product_materials_173 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.299, 'USD': 0.157, 'EUR': 0}
# insert_daily_costs("Product 173", product_materials_173)
#
# product_materials_174 = {'Aluminum 1Kg': 0.048, 'Copper 1Kg': 0, 'Gold 1Kg': 0.067, 'Silver 1Kg': 0.405, 'Ham_Petrol_Fiyati 1L': 0.224, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.378, 'Dogal_Gaz 100m^3': 0, 'USD': 0.236, 'EUR': 0.026}
# insert_daily_costs("Product 174", product_materials_174)
#
# product_materials_175 = {'Aluminum 1Kg': 0.107, 'Copper 1Kg': 0.308, 'Gold 1Kg': 0.477, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.446, 'Elektrik_Ucreti 1kW': 0.393, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.082, 'EUR': 0.27}
# insert_daily_costs("Product 175", product_materials_175)
#
# product_materials_176 = {'Aluminum 1Kg': 0.246, 'Copper 1Kg': 0.063, 'Gold 1Kg': 0.297, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.046, 'Asgari_Ucret 1 iş günü': 0.014, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 176", product_materials_176)
#
# product_materials_177 = {'Aluminum 1Kg': 0.202, 'Copper 1Kg': 0.224, 'Gold 1Kg': 0.421, 'Silver 1Kg': 0.204, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.04, 'Asgari_Ucret 1 iş günü': 0.007, 'Dogal_Gaz 100m^3': 0, 'USD': 0.151, 'EUR': 0.236}
# insert_daily_costs("Product 177", product_materials_177)
#
# product_materials_178 = {'Aluminum 1Kg': 0.402, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.468, 'Ham_Petrol_Fiyati 1L': 0.437, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.342, 'Dogal_Gaz 100m^3': 0.377, 'USD': 0, 'EUR': 0.095}
# insert_daily_costs("Product 178", product_materials_178)
#
# product_materials_179 = {'Aluminum 1Kg': 0.492, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.063, 'Ham_Petrol_Fiyati 1L': 0.01, 'Elektrik_Ucreti 1kW': 0.128, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.168, 'USD': 0.14, 'EUR': 0.165}
# insert_daily_costs("Product 179", product_materials_179)
#
# product_materials_180 = {'Aluminum 1Kg': 0.017, 'Copper 1Kg': 0.127, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.022, 'Elektrik_Ucreti 1kW': 0.134, 'Asgari_Ucret 1 iş günü': 0.199, 'Dogal_Gaz 100m^3': 0, 'USD': 0.122, 'EUR': 0.178}
# insert_daily_costs("Product 180", product_materials_180)
#
# product_materials_181 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.272, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.296, 'EUR': 0}
# insert_daily_costs("Product 181", product_materials_181)
#
# product_materials_182 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.378, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.082, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 182", product_materials_182)
#
# product_materials_183 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.278, 'Gold 1Kg': 0.325, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.086, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 183", product_materials_183)
#
# product_materials_184 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.475, 'Ham_Petrol_Fiyati 1L': 0.249, 'Elektrik_Ucreti 1kW': 0.145, 'Asgari_Ucret 1 iş günü': 0.197, 'Dogal_Gaz 100m^3': 0, 'USD': 0.302, 'EUR': 0.11}
# insert_daily_costs("Product 184", product_materials_184)
#
# product_materials_185 = {'Aluminum 1Kg': 0.082, 'Copper 1Kg': 0.321, 'Gold 1Kg': 0, 'Silver 1Kg': 0.469, 'Ham_Petrol_Fiyati 1L': 0.472, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.37, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.343}
# insert_daily_costs("Product 185", product_materials_185)
#
# product_materials_186 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.251, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.015, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.338, 'Dogal_Gaz 100m^3': 0, 'USD': 0.314, 'EUR': 0}
# insert_daily_costs("Product 186", product_materials_186)
#
# product_materials_187 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.062, 'Dogal_Gaz 100m^3': 0.423, 'USD': 0.404, 'EUR': 0.212}
# insert_daily_costs("Product 187", product_materials_187)
#
# product_materials_188 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.243, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.091, 'Elektrik_Ucreti 1kW': 0.455, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.443}
# insert_daily_costs("Product 188", product_materials_188)
#
# product_materials_189 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.44, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.011, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.246, 'USD': 0.27, 'EUR': 0.476}
# insert_daily_costs("Product 189", product_materials_189)
#
# product_materials_190 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.467, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.491, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.328, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 190", product_materials_190)
#
# product_materials_191 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.081, 'Gold 1Kg': 0, 'Silver 1Kg': 0.4, 'Ham_Petrol_Fiyati 1L': 0.067, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.068, 'Dogal_Gaz 100m^3': 0.311, 'USD': 0.343, 'EUR': 0.358}
# insert_daily_costs("Product 191", product_materials_191)
#
# product_materials_192 = {'Aluminum 1Kg': 0.342, 'Copper 1Kg': 0.363, 'Gold 1Kg': 0.032, 'Silver 1Kg': 0.486, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.243, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.35, 'USD': 0.488, 'EUR': 0}
# insert_daily_costs("Product 192", product_materials_192)
#
# product_materials_193 = {'Aluminum 1Kg': 0.297, 'Copper 1Kg': 0.202, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.405, 'EUR': 0}
# insert_daily_costs("Product 193", product_materials_193)
#
# product_materials_194 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.081, 'Silver 1Kg': 0.059, 'Ham_Petrol_Fiyati 1L': 0.371, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.092, 'USD': 0, 'EUR': 0.251}
# insert_daily_costs("Product 194", product_materials_194)
#
# product_materials_195 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.168, 'Gold 1Kg': 0, 'Silver 1Kg': 0.039, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.457, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.271}
# insert_daily_costs("Product 195", product_materials_195)
#
# product_materials_196 = {'Aluminum 1Kg': 0.21, 'Copper 1Kg': 0, 'Gold 1Kg': 0.445, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.108, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.269, 'USD': 0, 'EUR': 0.303}
# insert_daily_costs("Product 196", product_materials_196)
#
# product_materials_197 = {'Aluminum 1Kg': 0.205, 'Copper 1Kg': 0.096, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.372, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.316, 'EUR': 0.193}
# insert_daily_costs("Product 197", product_materials_197)
#
# product_materials_198 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.317, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.276, 'EUR': 0}
# insert_daily_costs("Product 198", product_materials_198)
#
# product_materials_199 = {'Aluminum 1Kg': 0.053, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.485, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.453, 'USD': 0.422, 'EUR': 0}
# insert_daily_costs("Product 199", product_materials_199)
#
# product_materials_200 = {'Aluminum 1Kg': 0.243, 'Copper 1Kg': 0, 'Gold 1Kg': 0.344, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.132, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.199, 'Dogal_Gaz 100m^3': 0.306, 'USD': 0.401, 'EUR': 0.241}
# insert_daily_costs("Product 200", product_materials_200)
#
# product_materials_201 = {'Aluminum 1Kg': 0.015, 'Copper 1Kg': 0.155, 'Gold 1Kg': 0.432, 'Silver 1Kg': 0.074, 'Ham_Petrol_Fiyati 1L': 0.431, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.439, 'USD': 0, 'EUR': 0.338}
# insert_daily_costs("Product 201", product_materials_201)
#
# product_materials_202 = {'Aluminum 1Kg': 0.492, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.458, 'Asgari_Ucret 1 iş günü': 0.121, 'Dogal_Gaz 100m^3': 0, 'USD': 0.408, 'EUR': 0.487}
# insert_daily_costs("Product 202", product_materials_202)
#
# product_materials_203 = {'Aluminum 1Kg': 0.425, 'Copper 1Kg': 0, 'Gold 1Kg': 0.452, 'Silver 1Kg': 0.299, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.19, 'Asgari_Ucret 1 iş günü': 0.265, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.468}
# insert_daily_costs("Product 203", product_materials_203)
#
# product_materials_204 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.435, 'Silver 1Kg': 0.203, 'Ham_Petrol_Fiyati 1L': 0.15, 'Elektrik_Ucreti 1kW': 0.45, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.115, 'USD': 0.141, 'EUR': 0}
# insert_daily_costs("Product 204", product_materials_204)
#
# product_materials_205 = {'Aluminum 1Kg': 0.452, 'Copper 1Kg': 0.067, 'Gold 1Kg': 0, 'Silver 1Kg': 0.475, 'Ham_Petrol_Fiyati 1L': 0.009, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.068, 'Dogal_Gaz 100m^3': 0.238, 'USD': 0.355, 'EUR': 0.159}
# insert_daily_costs("Product 205", product_materials_205)
#
# product_materials_206 = {'Aluminum 1Kg': 0.014, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.266, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.155, 'USD': 0.377, 'EUR': 0}
# insert_daily_costs("Product 206", product_materials_206)
#
# product_materials_207 = {'Aluminum 1Kg': 0.069, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.316, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.356, 'USD': 0, 'EUR': 0.097}
# insert_daily_costs("Product 207", product_materials_207)
#
# product_materials_208 = {'Aluminum 1Kg': 0.05, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.029, 'Ham_Petrol_Fiyati 1L': 0.349, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.254, 'Dogal_Gaz 100m^3': 0.304, 'USD': 0.123, 'EUR': 0}
# insert_daily_costs("Product 208", product_materials_208)
#
# product_materials_209 = {'Aluminum 1Kg': 0.314, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.167, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.466, 'USD': 0.166, 'EUR': 0.258}
# insert_daily_costs("Product 209", product_materials_209)
#
# product_materials_210 = {'Aluminum 1Kg': 0.082, 'Copper 1Kg': 0.059, 'Gold 1Kg': 0.301, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.109, 'Dogal_Gaz 100m^3': 0, 'USD': 0.046, 'EUR': 0}
# insert_daily_costs("Product 210", product_materials_210)
#
# product_materials_211 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.154, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.235, 'Elektrik_Ucreti 1kW': 0.233, 'Asgari_Ucret 1 iş günü': 0.054, 'Dogal_Gaz 100m^3': 0.283, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 211", product_materials_211)
#
# product_materials_212 = {'Aluminum 1Kg': 0.401, 'Copper 1Kg': 0, 'Gold 1Kg': 0.246, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.083, 'Elektrik_Ucreti 1kW': 0.314, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.447, 'USD': 0.071, 'EUR': 0}
# insert_daily_costs("Product 212", product_materials_212)
#
# product_materials_213 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.245, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.358, 'Dogal_Gaz 100m^3': 0.422, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 213", product_materials_213)
#
# product_materials_214 = {'Aluminum 1Kg': 0.427, 'Copper 1Kg': 0.098, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.314, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.004, 'Dogal_Gaz 100m^3': 0.454, 'USD': 0.398, 'EUR': 0.43}
# insert_daily_costs("Product 214", product_materials_214)
#
# product_materials_215 = {'Aluminum 1Kg': 0.349, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.08, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.309, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 215", product_materials_215)
#
# product_materials_216 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.491, 'Gold 1Kg': 0.492, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.402, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.227, 'Dogal_Gaz 100m^3': 0, 'USD': 0.338, 'EUR': 0.388}
# insert_daily_costs("Product 216", product_materials_216)
#
# product_materials_217 = {'Aluminum 1Kg': 0.426, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.32, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.398, 'EUR': 0.47}
# insert_daily_costs("Product 217", product_materials_217)
#
# product_materials_218 = {'Aluminum 1Kg': 0.364, 'Copper 1Kg': 0, 'Gold 1Kg': 0.012, 'Silver 1Kg': 0.292, 'Ham_Petrol_Fiyati 1L': 0.364, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.449, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 218", product_materials_218)
#
# product_materials_219 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.273, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.419, 'EUR': 0.223}
# insert_daily_costs("Product 219", product_materials_219)
#
# product_materials_220 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.398, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.478, 'Elektrik_Ucreti 1kW': 0.369, 'Asgari_Ucret 1 iş günü': 0.196, 'Dogal_Gaz 100m^3': 0.327, 'USD': 0, 'EUR': 0.15}
# insert_daily_costs("Product 220", product_materials_220)
#
# product_materials_221 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.145, 'Asgari_Ucret 1 iş günü': 0.137, 'Dogal_Gaz 100m^3': 0.262, 'USD': 0.065, 'EUR': 0}
# insert_daily_costs("Product 221", product_materials_221)
#
# product_materials_222 = {'Aluminum 1Kg': 0.181, 'Copper 1Kg': 0, 'Gold 1Kg': 0.233, 'Silver 1Kg': 0.303, 'Ham_Petrol_Fiyati 1L': 0.144, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.389, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 222", product_materials_222)
#
# product_materials_223 = {'Aluminum 1Kg': 0.24, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.445, 'Asgari_Ucret 1 iş günü': 0.393, 'Dogal_Gaz 100m^3': 0.383, 'USD': 0.387, 'EUR': 0}
# insert_daily_costs("Product 223", product_materials_223)
#
# product_materials_224 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.081, 'Gold 1Kg': 0, 'Silver 1Kg': 0.378, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.127, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.464}
# insert_daily_costs("Product 224", product_materials_224)
#
# product_materials_225 = {'Aluminum 1Kg': 0.06, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.101, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.039, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 225", product_materials_225)
#
# product_materials_226 = {'Aluminum 1Kg': 0.321, 'Copper 1Kg': 0.319, 'Gold 1Kg': 0.252, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.351, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.243, 'USD': 0.463, 'EUR': 0}
# insert_daily_costs("Product 226", product_materials_226)
#
# product_materials_227 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.264, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.063, 'Asgari_Ucret 1 iş günü': 0.497, 'Dogal_Gaz 100m^3': 0, 'USD': 0.169, 'EUR': 0}
# insert_daily_costs("Product 227", product_materials_227)
#
# product_materials_228 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.192, 'Gold 1Kg': 0, 'Silver 1Kg': 0.226, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.135}
# insert_daily_costs("Product 228", product_materials_228)
#
# product_materials_229 = {'Aluminum 1Kg': 0.026, 'Copper 1Kg': 0.49, 'Gold 1Kg': 0, 'Silver 1Kg': 0.024, 'Ham_Petrol_Fiyati 1L': 0.478, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.359, 'Dogal_Gaz 100m^3': 0.048, 'USD': 0, 'EUR': 0.013}
# insert_daily_costs("Product 229", product_materials_229)
#
# product_materials_230 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.29, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.054, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.341, 'USD': 0, 'EUR': 0.089}
# insert_daily_costs("Product 230", product_materials_230)
#
# product_materials_231 = {'Aluminum 1Kg': 0.184, 'Copper 1Kg': 0.166, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.048, 'Elektrik_Ucreti 1kW': 0.023, 'Asgari_Ucret 1 iş günü': 0.47, 'Dogal_Gaz 100m^3': 0.294, 'USD': 0.288, 'EUR': 0.347}
# insert_daily_costs("Product 231", product_materials_231)
#
# product_materials_232 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.448, 'Gold 1Kg': 0.137, 'Silver 1Kg': 0.157, 'Ham_Petrol_Fiyati 1L': 0.141, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.034, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 232", product_materials_232)
#
# product_materials_233 = {'Aluminum 1Kg': 0.371, 'Copper 1Kg': 0.029, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.292, 'Elektrik_Ucreti 1kW': 0.066, 'Asgari_Ucret 1 iş günü': 0.041, 'Dogal_Gaz 100m^3': 0.146, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 233", product_materials_233)
#
# product_materials_234 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.161, 'Gold 1Kg': 0.14, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.079, 'Elektrik_Ucreti 1kW': 0.14, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 234", product_materials_234)
#
# product_materials_235 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.169, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.191, 'Elektrik_Ucreti 1kW': 0.247, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.29, 'EUR': 0}
# insert_daily_costs("Product 235", product_materials_235)
#
# product_materials_236 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.355, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.166, 'Asgari_Ucret 1 iş günü': 0.289, 'Dogal_Gaz 100m^3': 0.19, 'USD': 0, 'EUR': 0.029}
# insert_daily_costs("Product 236", product_materials_236)
#
# product_materials_237 = {'Aluminum 1Kg': 0.401, 'Copper 1Kg': 0, 'Gold 1Kg': 0.454, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.093, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.024, 'Dogal_Gaz 100m^3': 0.101, 'USD': 0, 'EUR': 0.447}
# insert_daily_costs("Product 237", product_materials_237)
#
# product_materials_238 = {'Aluminum 1Kg': 0.366, 'Copper 1Kg': 0.373, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.341, 'Elektrik_Ucreti 1kW': 0.247, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.015, 'USD': 0, 'EUR': 0.246}
# insert_daily_costs("Product 238", product_materials_238)
#
# product_materials_239 = {'Aluminum 1Kg': 0.344, 'Copper 1Kg': 0, 'Gold 1Kg': 0.308, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.426, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.165, 'Dogal_Gaz 100m^3': 0.285, 'USD': 0, 'EUR': 0.193}
# insert_daily_costs("Product 239", product_materials_239)
#
# product_materials_240 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.025, 'Silver 1Kg': 0.483, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.12, 'Asgari_Ucret 1 iş günü': 0.484, 'Dogal_Gaz 100m^3': 0, 'USD': 0.31, 'EUR': 0}
# insert_daily_costs("Product 240", product_materials_240)
#
# product_materials_241 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.381, 'Gold 1Kg': 0.444, 'Silver 1Kg': 0.426, 'Ham_Petrol_Fiyati 1L': 0.438, 'Elektrik_Ucreti 1kW': 0.256, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.396}
# insert_daily_costs("Product 241", product_materials_241)
#
# product_materials_242 = {'Aluminum 1Kg': 0.226, 'Copper 1Kg': 0.412, 'Gold 1Kg': 0.098, 'Silver 1Kg': 0.204, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.011, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.394, 'EUR': 0}
# insert_daily_costs("Product 242", product_materials_242)
#
# product_materials_243 = {'Aluminum 1Kg': 0.244, 'Copper 1Kg': 0, 'Gold 1Kg': 0.48, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.246, 'Elektrik_Ucreti 1kW': 0.052, 'Asgari_Ucret 1 iş günü': 0.334, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.057}
# insert_daily_costs("Product 243", product_materials_243)
#
# product_materials_244 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.354, 'Gold 1Kg': 0.219, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.272, 'Elektrik_Ucreti 1kW': 0.076, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.372, 'USD': 0, 'EUR': 0.011}
# insert_daily_costs("Product 244", product_materials_244)
#
# product_materials_245 = {'Aluminum 1Kg': 0.094, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.489, 'Ham_Petrol_Fiyati 1L': 0.354, 'Elektrik_Ucreti 1kW': 0.192, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.038}
# insert_daily_costs("Product 245", product_materials_245)
#
# product_materials_246 = {'Aluminum 1Kg': 0.076, 'Copper 1Kg': 0.298, 'Gold 1Kg': 0, 'Silver 1Kg': 0.169, 'Ham_Petrol_Fiyati 1L': 0.229, 'Elektrik_Ucreti 1kW': 0.262, 'Asgari_Ucret 1 iş günü': 0.108, 'Dogal_Gaz 100m^3': 0, 'USD': 0.201, 'EUR': 0.457}
# insert_daily_costs("Product 246", product_materials_246)
#
# product_materials_247 = {'Aluminum 1Kg': 0.376, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.455, 'Elektrik_Ucreti 1kW': 0.192, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.399, 'EUR': 0.128}
# insert_daily_costs("Product 247", product_materials_247)
#
# product_materials_248 = {'Aluminum 1Kg': 0.241, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.138, 'Ham_Petrol_Fiyati 1L': 0.151, 'Elektrik_Ucreti 1kW': 0.38, 'Asgari_Ucret 1 iş günü': 0.281, 'Dogal_Gaz 100m^3': 0.191, 'USD': 0, 'EUR': 0.441}
# insert_daily_costs("Product 248", product_materials_248)
#
# product_materials_249 = {'Aluminum 1Kg': 0.104, 'Copper 1Kg': 0.457, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.173, 'Elektrik_Ucreti 1kW': 0.31, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.349, 'EUR': 0}
# insert_daily_costs("Product 249", product_materials_249)
#
# product_materials_250 = {'Aluminum 1Kg': 0.443, 'Copper 1Kg': 0, 'Gold 1Kg': 0.217, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.323, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.094, 'Dogal_Gaz 100m^3': 0, 'USD': 0.127, 'EUR': 0.48}
# insert_daily_costs("Product 250", product_materials_250)
#
# product_materials_251 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.453, 'Silver 1Kg': 0.38, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.089, 'EUR': 0.193}
# insert_daily_costs("Product 251", product_materials_251)
#
# product_materials_252 = {'Aluminum 1Kg': 0.114, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.21, 'Asgari_Ucret 1 iş günü': 0.41, 'Dogal_Gaz 100m^3': 0, 'USD': 0.368, 'EUR': 0.032}
# insert_daily_costs("Product 252", product_materials_252)
#
# product_materials_253 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.131, 'Elektrik_Ucreti 1kW': 0.348, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.465, 'EUR': 0}
# insert_daily_costs("Product 253", product_materials_253)
#
# product_materials_254 = {'Aluminum 1Kg': 0.375, 'Copper 1Kg': 0.155, 'Gold 1Kg': 0, 'Silver 1Kg': 0.311, 'Ham_Petrol_Fiyati 1L': 0.114, 'Elektrik_Ucreti 1kW': 0.363, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.145, 'USD': 0.396, 'EUR': 0}
# insert_daily_costs("Product 254", product_materials_254)
#
# product_materials_255 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.25, 'Gold 1Kg': 0, 'Silver 1Kg': 0.181, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.404, 'Asgari_Ucret 1 iş günü': 0.253, 'Dogal_Gaz 100m^3': 0.197, 'USD': 0.192, 'EUR': 0}
# insert_daily_costs("Product 255", product_materials_255)
#
# product_materials_256 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.233, 'Gold 1Kg': 0, 'Silver 1Kg': 0.076, 'Ham_Petrol_Fiyati 1L': 0.141, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.482, 'USD': 0.216, 'EUR': 0.243}
# insert_daily_costs("Product 256", product_materials_256)
#
# product_materials_257 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.472, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.046, 'Asgari_Ucret 1 iş günü': 0.256, 'Dogal_Gaz 100m^3': 0, 'USD': 0.336, 'EUR': 0.199}
# insert_daily_costs("Product 257", product_materials_257)
#
# product_materials_258 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.175, 'Silver 1Kg': 0.287, 'Ham_Petrol_Fiyati 1L': 0.229, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.447, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 258", product_materials_258)
#
# product_materials_259 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.009, 'Gold 1Kg': 0, 'Silver 1Kg': 0.163, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.44, 'Asgari_Ucret 1 iş günü': 0.195, 'Dogal_Gaz 100m^3': 0, 'USD': 0.139, 'EUR': 0.227}
# insert_daily_costs("Product 259", product_materials_259)
#
# product_materials_260 = {'Aluminum 1Kg': 0.088, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.241, 'Ham_Petrol_Fiyati 1L': 0.141, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.387, 'Dogal_Gaz 100m^3': 0.375, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 260", product_materials_260)
#
# product_materials_261 = {'Aluminum 1Kg': 0.259, 'Copper 1Kg': 0, 'Gold 1Kg': 0.398, 'Silver 1Kg': 0.337, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.485, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.277}
# insert_daily_costs("Product 261", product_materials_261)
#
# product_materials_262 = {'Aluminum 1Kg': 0.001, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.464, 'Ham_Petrol_Fiyati 1L': 0.321, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.05, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.241}
# insert_daily_costs("Product 262", product_materials_262)
#
# product_materials_263 = {'Aluminum 1Kg': 0.183, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.225, 'Asgari_Ucret 1 iş günü': 0.462, 'Dogal_Gaz 100m^3': 0, 'USD': 0.193, 'EUR': 0.357}
# insert_daily_costs("Product 263", product_materials_263)
#
# product_materials_264 = {'Aluminum 1Kg': 0.283, 'Copper 1Kg': 0.385, 'Gold 1Kg': 0.101, 'Silver 1Kg': 0.487, 'Ham_Petrol_Fiyati 1L': 0.095, 'Elektrik_Ucreti 1kW': 0.387, 'Asgari_Ucret 1 iş günü': 0.411, 'Dogal_Gaz 100m^3': 0.308, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 264", product_materials_264)
#
# product_materials_265 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.325, 'Silver 1Kg': 0.364, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.047, 'Dogal_Gaz 100m^3': 0, 'USD': 0.381, 'EUR': 0.471}
# insert_daily_costs("Product 265", product_materials_265)
#
# product_materials_266 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.398, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.409, 'Dogal_Gaz 100m^3': 0, 'USD': 0.388, 'EUR': 0.33}
# insert_daily_costs("Product 266", product_materials_266)
#
# product_materials_267 = {'Aluminum 1Kg': 0.075, 'Copper 1Kg': 0.279, 'Gold 1Kg': 0.383, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.033, 'Asgari_Ucret 1 iş günü': 0.205, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 267", product_materials_267)
#
# product_materials_268 = {'Aluminum 1Kg': 0.093, 'Copper 1Kg': 0.302, 'Gold 1Kg': 0, 'Silver 1Kg': 0.478, 'Ham_Petrol_Fiyati 1L': 0.377, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.431, 'Dogal_Gaz 100m^3': 0.152, 'USD': 0.304, 'EUR': 0.068}
# insert_daily_costs("Product 268", product_materials_268)
#
# product_materials_269 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.325, 'Ham_Petrol_Fiyati 1L': 0.098, 'Elektrik_Ucreti 1kW': 0.376, 'Asgari_Ucret 1 iş günü': 0.064, 'Dogal_Gaz 100m^3': 0.15, 'USD': 0, 'EUR': 0.121}
# insert_daily_costs("Product 269", product_materials_269)
#
# product_materials_270 = {'Aluminum 1Kg': 0.185, 'Copper 1Kg': 0, 'Gold 1Kg': 0.499, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.197, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.258, 'Dogal_Gaz 100m^3': 0.074, 'USD': 0, 'EUR': 0.446}
# insert_daily_costs("Product 270", product_materials_270)
#
# product_materials_271 = {'Aluminum 1Kg': 0.493, 'Copper 1Kg': 0.021, 'Gold 1Kg': 0.471, 'Silver 1Kg': 0.052, 'Ham_Petrol_Fiyati 1L': 0.066, 'Elektrik_Ucreti 1kW': 0.257, 'Asgari_Ucret 1 iş günü': 0.069, 'Dogal_Gaz 100m^3': 0, 'USD': 0.167, 'EUR': 0}
# insert_daily_costs("Product 271", product_materials_271)
#
# product_materials_272 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.057, 'Gold 1Kg': 0.205, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.036, 'Dogal_Gaz 100m^3': 0.241, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 272", product_materials_272)
#
# product_materials_273 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.273, 'Gold 1Kg': 0.353, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.078, 'USD': 0, 'EUR': 0.347}
# insert_daily_costs("Product 273", product_materials_273)
#
# product_materials_274 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.081, 'Silver 1Kg': 0.237, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.371, 'Asgari_Ucret 1 iş günü': 0.004, 'Dogal_Gaz 100m^3': 0.209, 'USD': 0.207, 'EUR': 0.162}
# insert_daily_costs("Product 274", product_materials_274)
#
# product_materials_275 = {'Aluminum 1Kg': 0.087, 'Copper 1Kg': 0, 'Gold 1Kg': 0.34, 'Silver 1Kg': 0.303, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.258, 'Asgari_Ucret 1 iş günü': 0.183, 'Dogal_Gaz 100m^3': 0.085, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 275", product_materials_275)
#
# product_materials_276 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.009, 'Gold 1Kg': 0.059, 'Silver 1Kg': 0.305, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.23, 'USD': 0.344, 'EUR': 0}
# insert_daily_costs("Product 276", product_materials_276)
#
# product_materials_277 = {'Aluminum 1Kg': 0.031, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.408, 'Elektrik_Ucreti 1kW': 0.444, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.488, 'USD': 0, 'EUR': 0.089}
# insert_daily_costs("Product 277", product_materials_277)
#
# product_materials_278 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.411, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.493, 'Asgari_Ucret 1 iş günü': 0.299, 'Dogal_Gaz 100m^3': 0.343, 'USD': 0, 'EUR': 0.116}
# insert_daily_costs("Product 278", product_materials_278)
#
# product_materials_279 = {'Aluminum 1Kg': 0.141, 'Copper 1Kg': 0.423, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.053, 'Elektrik_Ucreti 1kW': 0.042, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.163, 'USD': 0, 'EUR': 0.31}
# insert_daily_costs("Product 279", product_materials_279)
#
# product_materials_280 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.127, 'Gold 1Kg': 0.23, 'Silver 1Kg': 0.191, 'Ham_Petrol_Fiyati 1L': 0.3, 'Elektrik_Ucreti 1kW': 0.426, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.254, 'EUR': 0}
# insert_daily_costs("Product 280", product_materials_280)
#
# product_materials_281 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.354, 'Gold 1Kg': 0.112, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.139, 'Elektrik_Ucreti 1kW': 0.243, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.359, 'EUR': 0}
# insert_daily_costs("Product 281", product_materials_281)
#
# product_materials_282 = {'Aluminum 1Kg': 0.219, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.115, 'Elektrik_Ucreti 1kW': 0.486, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.463, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 282", product_materials_282)
#
# product_materials_283 = {'Aluminum 1Kg': 0.161, 'Copper 1Kg': 0.103, 'Gold 1Kg': 0, 'Silver 1Kg': 0.363, 'Ham_Petrol_Fiyati 1L': 0.151, 'Elektrik_Ucreti 1kW': 0.437, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 283", product_materials_283)
#
# product_materials_284 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.145, 'Gold 1Kg': 0.192, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.114, 'Elektrik_Ucreti 1kW': 0.064, 'Asgari_Ucret 1 iş günü': 0.195, 'Dogal_Gaz 100m^3': 0.275, 'USD': 0, 'EUR': 0.227}
# insert_daily_costs("Product 284", product_materials_284)
#
# product_materials_285 = {'Aluminum 1Kg': 0.421, 'Copper 1Kg': 0.298, 'Gold 1Kg': 0.302, 'Silver 1Kg': 0.119, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.107, 'Asgari_Ucret 1 iş günü': 0.305, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.238}
# insert_daily_costs("Product 285", product_materials_285)
#
# product_materials_286 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.263, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.198, 'Elektrik_Ucreti 1kW': 0.177, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 286", product_materials_286)
#
# product_materials_287 = {'Aluminum 1Kg': 0.498, 'Copper 1Kg': 0.061, 'Gold 1Kg': 0, 'Silver 1Kg': 0.148, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.024, 'Asgari_Ucret 1 iş günü': 0.22, 'Dogal_Gaz 100m^3': 0, 'USD': 0.283, 'EUR': 0.162}
# insert_daily_costs("Product 287", product_materials_287)
#
# product_materials_288 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.23, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.112, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.292, 'USD': 0.269, 'EUR': 0.441}
# insert_daily_costs("Product 288", product_materials_288)
#
# product_materials_289 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.428, 'Gold 1Kg': 0, 'Silver 1Kg': 0.25, 'Ham_Petrol_Fiyati 1L': 0.417, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.259}
# insert_daily_costs("Product 289", product_materials_289)
#
# product_materials_290 = {'Aluminum 1Kg': 0.27, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.485, 'Asgari_Ucret 1 iş günü': 0.101, 'Dogal_Gaz 100m^3': 0.168, 'USD': 0, 'EUR': 0.457}
# insert_daily_costs("Product 290", product_materials_290)
#
# product_materials_291 = {'Aluminum 1Kg': 0.204, 'Copper 1Kg': 0, 'Gold 1Kg': 0.389, 'Silver 1Kg': 0.405, 'Ham_Petrol_Fiyati 1L': 0.388, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.13, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.138}
# insert_daily_costs("Product 291", product_materials_291)
#
# product_materials_292 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.066, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.328, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.351, 'EUR': 0.46}
# insert_daily_costs("Product 292", product_materials_292)
#
# product_materials_293 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.003, 'Asgari_Ucret 1 iş günü': 0.116, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.439}
# insert_daily_costs("Product 293", product_materials_293)
#
# product_materials_294 = {'Aluminum 1Kg': 0.228, 'Copper 1Kg': 0.207, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.392, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.36, 'USD': 0.071, 'EUR': 0.339}
# insert_daily_costs("Product 294", product_materials_294)
#
# product_materials_295 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.481, 'Gold 1Kg': 0.005, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.317, 'Dogal_Gaz 100m^3': 0.195, 'USD': 0, 'EUR': 0.249}
# insert_daily_costs("Product 295", product_materials_295)
#
# product_materials_296 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.363, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.342, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.221, 'EUR': 0.109}
# insert_daily_costs("Product 296", product_materials_296)
#
# product_materials_297 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.012, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.057, 'EUR': 0.297}
# insert_daily_costs("Product 297", product_materials_297)
#
# product_materials_298 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.318, 'Elektrik_Ucreti 1kW': 0.019, 'Asgari_Ucret 1 iş günü': 0.095, 'Dogal_Gaz 100m^3': 0.379, 'USD': 0, 'EUR': 0.084}
# insert_daily_costs("Product 298", product_materials_298)
#
# product_materials_299 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.479, 'Gold 1Kg': 0, 'Silver 1Kg': 0.326, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.491, 'Asgari_Ucret 1 iş günü': 0.181, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 299", product_materials_299)
#
# product_materials_300 = {'Aluminum 1Kg': 0.392, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.026, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.124}
# insert_daily_costs("Product 300", product_materials_300)
#
# product_materials_301 = {'Aluminum 1Kg': 0.082, 'Copper 1Kg': 0.487, 'Gold 1Kg': 0, 'Silver 1Kg': 0.356, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.419, 'Asgari_Ucret 1 iş günü': 0.481, 'Dogal_Gaz 100m^3': 0, 'USD': 0.459, 'EUR': 0}
# insert_daily_costs("Product 301", product_materials_301)
#
# product_materials_302 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.005, 'Gold 1Kg': 0, 'Silver 1Kg': 0.473, 'Ham_Petrol_Fiyati 1L': 0.146, 'Elektrik_Ucreti 1kW': 0.065, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.013, 'USD': 0.363, 'EUR': 0.12}
# insert_daily_costs("Product 302", product_materials_302)
#
# product_materials_303 = {'Aluminum 1Kg': 0.13, 'Copper 1Kg': 0, 'Gold 1Kg': 0.291, 'Silver 1Kg': 0.167, 'Ham_Petrol_Fiyati 1L': 0.321, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.129, 'Dogal_Gaz 100m^3': 0, 'USD': 0.323, 'EUR': 0.163}
# insert_daily_costs("Product 303", product_materials_303)
#
# product_materials_304 = {'Aluminum 1Kg': 0.144, 'Copper 1Kg': 0, 'Gold 1Kg': 0.113, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.351, 'Asgari_Ucret 1 iş günü': 0.224, 'Dogal_Gaz 100m^3': 0.065, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 304", product_materials_304)
#
# product_materials_305 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.204, 'Silver 1Kg': 0.384, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.311, 'Asgari_Ucret 1 iş günü': 0.04, 'Dogal_Gaz 100m^3': 0.459, 'USD': 0.074, 'EUR': 0}
# insert_daily_costs("Product 305", product_materials_305)
#
# product_materials_306 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.265, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.198, 'Asgari_Ucret 1 iş günü': 0.146, 'Dogal_Gaz 100m^3': 0, 'USD': 0.479, 'EUR': 0}
# insert_daily_costs("Product 306", product_materials_306)
#
# product_materials_307 = {'Aluminum 1Kg': 0.017, 'Copper 1Kg': 0.038, 'Gold 1Kg': 0, 'Silver 1Kg': 0.041, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.303, 'Dogal_Gaz 100m^3': 0.273, 'USD': 0.136, 'EUR': 0.317}
# insert_daily_costs("Product 307", product_materials_307)
#
# product_materials_308 = {'Aluminum 1Kg': 0.135, 'Copper 1Kg': 0.263, 'Gold 1Kg': 0.34, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.357, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.313, 'USD': 0.001, 'EUR': 0}
# insert_daily_costs("Product 308", product_materials_308)
#
# product_materials_309 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.31, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.376, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.019, 'EUR': 0.077}
# insert_daily_costs("Product 309", product_materials_309)
#
# product_materials_310 = {'Aluminum 1Kg': 0.23, 'Copper 1Kg': 0.481, 'Gold 1Kg': 0.156, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.177, 'Elektrik_Ucreti 1kW': 0.397, 'Asgari_Ucret 1 iş günü': 0.455, 'Dogal_Gaz 100m^3': 0.285, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 310", product_materials_310)
#
# product_materials_311 = {'Aluminum 1Kg': 0.017, 'Copper 1Kg': 0.439, 'Gold 1Kg': 0.214, 'Silver 1Kg': 0.246, 'Ham_Petrol_Fiyati 1L': 0.316, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.29}
# insert_daily_costs("Product 311", product_materials_311)
#
# product_materials_312 = {'Aluminum 1Kg': 0.463, 'Copper 1Kg': 0, 'Gold 1Kg': 0.387, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.042, 'Elektrik_Ucreti 1kW': 0.046, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.471, 'USD': 0.246, 'EUR': 0}
# insert_daily_costs("Product 312", product_materials_312)
#
# product_materials_313 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.088, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.409, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.097, 'Dogal_Gaz 100m^3': 0.142, 'USD': 0.214, 'EUR': 0}
# insert_daily_costs("Product 313", product_materials_313)
#
# product_materials_314 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.07, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.016, 'Elektrik_Ucreti 1kW': 0.11, 'Asgari_Ucret 1 iş günü': 0.256, 'Dogal_Gaz 100m^3': 0.288, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 314", product_materials_314)
#
# product_materials_315 = {'Aluminum 1Kg': 0.073, 'Copper 1Kg': 0.449, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.319, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.403, 'Dogal_Gaz 100m^3': 0, 'USD': 0.051, 'EUR': 0}
# insert_daily_costs("Product 315", product_materials_315)
#
# product_materials_316 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.408, 'Gold 1Kg': 0, 'Silver 1Kg': 0.052, 'Ham_Petrol_Fiyati 1L': 0.038, 'Elektrik_Ucreti 1kW': 0.383, 'Asgari_Ucret 1 iş günü': 0.069, 'Dogal_Gaz 100m^3': 0.397, 'USD': 0.429, 'EUR': 0}
# insert_daily_costs("Product 316", product_materials_316)
#
# product_materials_317 = {'Aluminum 1Kg': 0.086, 'Copper 1Kg': 0, 'Gold 1Kg': 0.266, 'Silver 1Kg': 0.057, 'Ham_Petrol_Fiyati 1L': 0.039, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.392, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 317", product_materials_317)
#
# product_materials_318 = {'Aluminum 1Kg': 0.234, 'Copper 1Kg': 0.193, 'Gold 1Kg': 0, 'Silver 1Kg': 0.471, 'Ham_Petrol_Fiyati 1L': 0.298, 'Elektrik_Ucreti 1kW': 0.142, 'Asgari_Ucret 1 iş günü': 0.115, 'Dogal_Gaz 100m^3': 0.385, 'USD': 0.378, 'EUR': 0.031}
# insert_daily_costs("Product 318", product_materials_318)
#
# product_materials_319 = {'Aluminum 1Kg': 0.014, 'Copper 1Kg': 0.272, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.206, 'Elektrik_Ucreti 1kW': 0.104, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.262}
# insert_daily_costs("Product 319", product_materials_319)
#
# product_materials_320 = {'Aluminum 1Kg': 0.068, 'Copper 1Kg': 0.48, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.481, 'Elektrik_Ucreti 1kW': 0.403, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.002, 'USD': 0.43, 'EUR': 0}
# insert_daily_costs("Product 320", product_materials_320)
#
# product_materials_321 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.448, 'Gold 1Kg': 0, 'Silver 1Kg': 0.141, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.043, 'Asgari_Ucret 1 iş günü': 0.139, 'Dogal_Gaz 100m^3': 0.45, 'USD': 0.325, 'EUR': 0.278}
# insert_daily_costs("Product 321", product_materials_321)
#
# product_materials_322 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.434, 'Ham_Petrol_Fiyati 1L': 0.46, 'Elektrik_Ucreti 1kW': 0.297, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.227, 'USD': 0.29, 'EUR': 0.137}
# insert_daily_costs("Product 322", product_materials_322)
#
# product_materials_323 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.258, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.325, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.28, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 323", product_materials_323)
#
# product_materials_324 = {'Aluminum 1Kg': 0.441, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.016, 'Ham_Petrol_Fiyati 1L': 0.167, 'Elektrik_Ucreti 1kW': 0.321, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.279, 'USD': 0.17, 'EUR': 0}
# insert_daily_costs("Product 324", product_materials_324)
#
# product_materials_325 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.266, 'Elektrik_Ucreti 1kW': 0.076, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.372, 'USD': 0.168, 'EUR': 0}
# insert_daily_costs("Product 325", product_materials_325)
#
# product_materials_326 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.441, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.494, 'Asgari_Ucret 1 iş günü': 0.255, 'Dogal_Gaz 100m^3': 0.322, 'USD': 0.277, 'EUR': 0.278}
# insert_daily_costs("Product 326", product_materials_326)
#
# product_materials_327 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.002, 'Gold 1Kg': 0, 'Silver 1Kg': 0.114, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.296, 'Dogal_Gaz 100m^3': 0.036, 'USD': 0, 'EUR': 0.198}
# insert_daily_costs("Product 327", product_materials_327)
#
# product_materials_328 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.45, 'Gold 1Kg': 0, 'Silver 1Kg': 0.315, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.12, 'Asgari_Ucret 1 iş günü': 0.421, 'Dogal_Gaz 100m^3': 0.368, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 328", product_materials_328)
#
# product_materials_329 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.102, 'Gold 1Kg': 0.343, 'Silver 1Kg': 0.431, 'Ham_Petrol_Fiyati 1L': 0.493, 'Elektrik_Ucreti 1kW': 0.288, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.174, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 329", product_materials_329)
#
# product_materials_330 = {'Aluminum 1Kg': 0.426, 'Copper 1Kg': 0, 'Gold 1Kg': 0.067, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.311, 'Elektrik_Ucreti 1kW': 0.072, 'Asgari_Ucret 1 iş günü': 0.343, 'Dogal_Gaz 100m^3': 0, 'USD': 0.058, 'EUR': 0.412}
# insert_daily_costs("Product 330", product_materials_330)
#
# product_materials_331 = {'Aluminum 1Kg': 0.077, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.115, 'Elektrik_Ucreti 1kW': 0.442, 'Asgari_Ucret 1 iş günü': 0.035, 'Dogal_Gaz 100m^3': 0.399, 'USD': 0.392, 'EUR': 0}
# insert_daily_costs("Product 331", product_materials_331)
#
# product_materials_332 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.011, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.078, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.397}
# insert_daily_costs("Product 332", product_materials_332)
#
# product_materials_333 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.322, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.331, 'Asgari_Ucret 1 iş günü': 0.214, 'Dogal_Gaz 100m^3': 0.395, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 333", product_materials_333)
#
# product_materials_334 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.01, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.012, 'Dogal_Gaz 100m^3': 0.138, 'USD': 0.11, 'EUR': 0}
# insert_daily_costs("Product 334", product_materials_334)
#
# product_materials_335 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.369, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.05, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.421, 'USD': 0, 'EUR': 0.305}
# insert_daily_costs("Product 335", product_materials_335)
#
# product_materials_336 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.045, 'Gold 1Kg': 0, 'Silver 1Kg': 0.264, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.165, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.23, 'EUR': 0}
# insert_daily_costs("Product 336", product_materials_336)
#
# product_materials_337 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.06, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.238, 'Elektrik_Ucreti 1kW': 0.225, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.11, 'USD': 0, 'EUR': 0.151}
# insert_daily_costs("Product 337", product_materials_337)
#
# product_materials_338 = {'Aluminum 1Kg': 0.366, 'Copper 1Kg': 0.1, 'Gold 1Kg': 0.327, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.052, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.285, 'USD': 0.425, 'EUR': 0}
# insert_daily_costs("Product 338", product_materials_338)
#
# product_materials_339 = {'Aluminum 1Kg': 0.213, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.443, 'Elektrik_Ucreti 1kW': 0.274, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.494, 'EUR': 0.282}
# insert_daily_costs("Product 339", product_materials_339)
#
# product_materials_340 = {'Aluminum 1Kg': 0.122, 'Copper 1Kg': 0, 'Gold 1Kg': 0.003, 'Silver 1Kg': 0.306, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.323, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.127}
# insert_daily_costs("Product 340", product_materials_340)
#
# product_materials_341 = {'Aluminum 1Kg': 0.149, 'Copper 1Kg': 0.358, 'Gold 1Kg': 0.207, 'Silver 1Kg': 0.279, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.053, 'USD': 0.454, 'EUR': 0.175}
# insert_daily_costs("Product 341", product_materials_341)
#
# product_materials_342 = {'Aluminum 1Kg': 0.41, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.045, 'Ham_Petrol_Fiyati 1L': 0.487, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.118, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.262}
# insert_daily_costs("Product 342", product_materials_342)
#
# product_materials_343 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.186, 'Gold 1Kg': 0.096, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.405, 'Dogal_Gaz 100m^3': 0, 'USD': 0.423, 'EUR': 0.22}
# insert_daily_costs("Product 343", product_materials_343)
#
# product_materials_344 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.316, 'Silver 1Kg': 0.047, 'Ham_Petrol_Fiyati 1L': 0.338, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.283, 'Dogal_Gaz 100m^3': 0.321, 'USD': 0, 'EUR': 0.146}
# insert_daily_costs("Product 344", product_materials_344)
#
# product_materials_345 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.318, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.398, 'Dogal_Gaz 100m^3': 0, 'USD': 0.262, 'EUR': 0.03}
# insert_daily_costs("Product 345", product_materials_345)
#
# product_materials_346 = {'Aluminum 1Kg': 0.155, 'Copper 1Kg': 0.025, 'Gold 1Kg': 0.394, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.096, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.18, 'USD': 0.041, 'EUR': 0}
# insert_daily_costs("Product 346", product_materials_346)
#
# product_materials_347 = {'Aluminum 1Kg': 0.418, 'Copper 1Kg': 0, 'Gold 1Kg': 0.451, 'Silver 1Kg': 0.36, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.376, 'USD': 0.036, 'EUR': 0}
# insert_daily_costs("Product 347", product_materials_347)
#
# product_materials_348 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.296, 'Silver 1Kg': 0.094, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.189, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.175, 'USD': 0.267, 'EUR': 0}
# insert_daily_costs("Product 348", product_materials_348)
#
# product_materials_349 = {'Aluminum 1Kg': 0.104, 'Copper 1Kg': 0.207, 'Gold 1Kg': 0, 'Silver 1Kg': 0.39, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.187, 'Asgari_Ucret 1 iş günü': 0.363, 'Dogal_Gaz 100m^3': 0, 'USD': 0.176, 'EUR': 0.068}
# insert_daily_costs("Product 349", product_materials_349)
#
# product_materials_350 = {'Aluminum 1Kg': 0.228, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.349, 'Dogal_Gaz 100m^3': 0.02, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 350", product_materials_350)
#
# product_materials_351 = {'Aluminum 1Kg': 0.267, 'Copper 1Kg': 0.053, 'Gold 1Kg': 0.09, 'Silver 1Kg': 0.23, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.387, 'Asgari_Ucret 1 iş günü': 0.115, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 351", product_materials_351)
#
# product_materials_352 = {'Aluminum 1Kg': 0.236, 'Copper 1Kg': 0.08, 'Gold 1Kg': 0.329, 'Silver 1Kg': 0.142, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.152, 'Dogal_Gaz 100m^3': 0.274, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 352", product_materials_352)
#
# product_materials_353 = {'Aluminum 1Kg': 0.337, 'Copper 1Kg': 0, 'Gold 1Kg': 0.208, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.26, 'Elektrik_Ucreti 1kW': 0.393, 'Asgari_Ucret 1 iş günü': 0.175, 'Dogal_Gaz 100m^3': 0.071, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 353", product_materials_353)
#
# product_materials_354 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.19, 'Gold 1Kg': 0.231, 'Silver 1Kg': 0.145, 'Ham_Petrol_Fiyati 1L': 0.305, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.226, 'Dogal_Gaz 100m^3': 0.156, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 354", product_materials_354)
#
# product_materials_355 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.1, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.307}
# insert_daily_costs("Product 355", product_materials_355)
#
# product_materials_356 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.328, 'Gold 1Kg': 0.14, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.428, 'Elektrik_Ucreti 1kW': 0.165, 'Asgari_Ucret 1 iş günü': 0.113, 'Dogal_Gaz 100m^3': 0.187, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 356", product_materials_356)
#
# product_materials_357 = {'Aluminum 1Kg': 0.246, 'Copper 1Kg': 0, 'Gold 1Kg': 0.043, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.358, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.191, 'Dogal_Gaz 100m^3': 0, 'USD': 0.016, 'EUR': 0.367}
# insert_daily_costs("Product 357", product_materials_357)
#
# product_materials_358 = {'Aluminum 1Kg': 0.222, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.017, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.027, 'Asgari_Ucret 1 iş günü': 0.097, 'Dogal_Gaz 100m^3': 0.482, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 358", product_materials_358)
#
# product_materials_359 = {'Aluminum 1Kg': 0.232, 'Copper 1Kg': 0, 'Gold 1Kg': 0.093, 'Silver 1Kg': 0.431, 'Ham_Petrol_Fiyati 1L': 0.353, 'Elektrik_Ucreti 1kW': 0.401, 'Asgari_Ucret 1 iş günü': 0.493, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 359", product_materials_359)
#
# product_materials_360 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.478, 'Silver 1Kg': 0.055, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.156, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.136, 'EUR': 0}
# insert_daily_costs("Product 360", product_materials_360)
#
# product_materials_361 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.36, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 361", product_materials_361)
#
# product_materials_362 = {'Aluminum 1Kg': 0.359, 'Copper 1Kg': 0.2, 'Gold 1Kg': 0, 'Silver 1Kg': 0.364, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.116, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 362", product_materials_362)
#
# product_materials_363 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.325, 'Silver 1Kg': 0.009, 'Ham_Petrol_Fiyati 1L': 0.165, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.346, 'Dogal_Gaz 100m^3': 0, 'USD': 0.413, 'EUR': 0}
# insert_daily_costs("Product 363", product_materials_363)
#
# product_materials_364 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.438, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.485, 'Asgari_Ucret 1 iş günü': 0.479, 'Dogal_Gaz 100m^3': 0.091, 'USD': 0, 'EUR': 0.377}
# insert_daily_costs("Product 364", product_materials_364)
#
# product_materials_365 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.388, 'Silver 1Kg': 0.441, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.166, 'Dogal_Gaz 100m^3': 0.409, 'USD': 0.085, 'EUR': 0}
# insert_daily_costs("Product 365", product_materials_365)
#
# product_materials_366 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.07, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.324, 'Dogal_Gaz 100m^3': 0.027, 'USD': 0.111, 'EUR': 0}
# insert_daily_costs("Product 366", product_materials_366)
#
# product_materials_367 = {'Aluminum 1Kg': 0.38, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.31, 'Elektrik_Ucreti 1kW': 0.115, 'Asgari_Ucret 1 iş günü': 0.073, 'Dogal_Gaz 100m^3': 0.059, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 367", product_materials_367)
#
# product_materials_368 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.207, 'Gold 1Kg': 0.091, 'Silver 1Kg': 0.412, 'Ham_Petrol_Fiyati 1L': 0.472, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.116, 'Dogal_Gaz 100m^3': 0, 'USD': 0.401, 'EUR': 0}
# insert_daily_costs("Product 368", product_materials_368)
#
# product_materials_369 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.244, 'Silver 1Kg': 0.137, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.149, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 369", product_materials_369)
#
# product_materials_370 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.004, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.43, 'EUR': 0.427}
# insert_daily_costs("Product 370", product_materials_370)
#
# product_materials_371 = {'Aluminum 1Kg': 0.309, 'Copper 1Kg': 0.061, 'Gold 1Kg': 0, 'Silver 1Kg': 0.342, 'Ham_Petrol_Fiyati 1L': 0.138, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.362, 'Dogal_Gaz 100m^3': 0, 'USD': 0.02, 'EUR': 0.18}
# insert_daily_costs("Product 371", product_materials_371)
#
# product_materials_372 = {'Aluminum 1Kg': 0.089, 'Copper 1Kg': 0, 'Gold 1Kg': 0.244, 'Silver 1Kg': 0.478, 'Ham_Petrol_Fiyati 1L': 0.011, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.331, 'Dogal_Gaz 100m^3': 0.284, 'USD': 0.012, 'EUR': 0}
# insert_daily_costs("Product 372", product_materials_372)
#
# product_materials_373 = {'Aluminum 1Kg': 0.458, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.203, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.268, 'Asgari_Ucret 1 iş günü': 0.166, 'Dogal_Gaz 100m^3': 0.226, 'USD': 0.402, 'EUR': 0}
# insert_daily_costs("Product 373", product_materials_373)
#
# product_materials_374 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.068, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.172, 'Dogal_Gaz 100m^3': 0.028, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 374", product_materials_374)
#
# product_materials_375 = {'Aluminum 1Kg': 0.157, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.192, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.452, 'Dogal_Gaz 100m^3': 0.152, 'USD': 0.19, 'EUR': 0}
# insert_daily_costs("Product 375", product_materials_375)
#
# product_materials_376 = {'Aluminum 1Kg': 0.083, 'Copper 1Kg': 0, 'Gold 1Kg': 0.455, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.028, 'Asgari_Ucret 1 iş günü': 0.105, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 376", product_materials_376)
#
# product_materials_377 = {'Aluminum 1Kg': 0.395, 'Copper 1Kg': 0, 'Gold 1Kg': 0.411, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.196, 'Asgari_Ucret 1 iş günü': 0.256, 'Dogal_Gaz 100m^3': 0, 'USD': 0.233, 'EUR': 0}
# insert_daily_costs("Product 377", product_materials_377)
#
# product_materials_378 = {'Aluminum 1Kg': 0.266, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.488, 'Asgari_Ucret 1 iş günü': 0.181, 'Dogal_Gaz 100m^3': 0.1, 'USD': 0.109, 'EUR': 0.466}
# insert_daily_costs("Product 378", product_materials_378)
#
# product_materials_379 = {'Aluminum 1Kg': 0.392, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.425, 'Ham_Petrol_Fiyati 1L': 0.233, 'Elektrik_Ucreti 1kW': 0.337, 'Asgari_Ucret 1 iş günü': 0.181, 'Dogal_Gaz 100m^3': 0.071, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 379", product_materials_379)
#
# product_materials_380 = {'Aluminum 1Kg': 0.37, 'Copper 1Kg': 0, 'Gold 1Kg': 0.18, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.15, 'USD': 0.456, 'EUR': 0}
# insert_daily_costs("Product 380", product_materials_380)
#
# product_materials_381 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.469, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.382, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 381", product_materials_381)
#
# product_materials_382 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.062, 'Gold 1Kg': 0, 'Silver 1Kg': 0.036, 'Ham_Petrol_Fiyati 1L': 0.064, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.274, 'Dogal_Gaz 100m^3': 0, 'USD': 0.235, 'EUR': 0.194}
# insert_daily_costs("Product 382", product_materials_382)
#
# product_materials_383 = {'Aluminum 1Kg': 0.211, 'Copper 1Kg': 0, 'Gold 1Kg': 0.385, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.102, 'Asgari_Ucret 1 iş günü': 0.185, 'Dogal_Gaz 100m^3': 0.31, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 383", product_materials_383)
#
# product_materials_384 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.076, 'Dogal_Gaz 100m^3': 0.478, 'USD': 0.211, 'EUR': 0.073}
# insert_daily_costs("Product 384", product_materials_384)
#
# product_materials_385 = {'Aluminum 1Kg': 0.499, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.071, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.192, 'Dogal_Gaz 100m^3': 0, 'USD': 0.112, 'EUR': 0.316}
# insert_daily_costs("Product 385", product_materials_385)
#
# product_materials_386 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.289, 'Gold 1Kg': 0.386, 'Silver 1Kg': 0.456, 'Ham_Petrol_Fiyati 1L': 0.053, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.103, 'Dogal_Gaz 100m^3': 0, 'USD': 0.069, 'EUR': 0}
# insert_daily_costs("Product 386", product_materials_386)
#
# product_materials_387 = {'Aluminum 1Kg': 0.08, 'Copper 1Kg': 0, 'Gold 1Kg': 0.028, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.02, 'Asgari_Ucret 1 iş günü': 0.136, 'Dogal_Gaz 100m^3': 0, 'USD': 0.221, 'EUR': 0}
# insert_daily_costs("Product 387", product_materials_387)
#
# product_materials_388 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.371, 'Gold 1Kg': 0.117, 'Silver 1Kg': 0.061, 'Ham_Petrol_Fiyati 1L': 0.07, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.459, 'Dogal_Gaz 100m^3': 0, 'USD': 0.225, 'EUR': 0}
# insert_daily_costs("Product 388", product_materials_388)
#
# product_materials_389 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.066, 'Gold 1Kg': 0, 'Silver 1Kg': 0.02, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.361, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.19, 'USD': 0, 'EUR': 0.36}
# insert_daily_costs("Product 389", product_materials_389)
#
# product_materials_390 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.272, 'Gold 1Kg': 0, 'Silver 1Kg': 0.072, 'Ham_Petrol_Fiyati 1L': 0.163, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.077, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 390", product_materials_390)
#
# product_materials_391 = {'Aluminum 1Kg': 0.44, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.165, 'Ham_Petrol_Fiyati 1L': 0.347, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.28, 'Dogal_Gaz 100m^3': 0.271, 'USD': 0, 'EUR': 0.017}
# insert_daily_costs("Product 391", product_materials_391)
#
# product_materials_392 = {'Aluminum 1Kg': 0.442, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.34, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.192, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 392", product_materials_392)
#
# product_materials_393 = {'Aluminum 1Kg': 0.477, 'Copper 1Kg': 0.13, 'Gold 1Kg': 0.219, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.199, 'Elektrik_Ucreti 1kW': 0.476, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.103, 'USD': 0.013, 'EUR': 0.361}
# insert_daily_costs("Product 393", product_materials_393)
#
# product_materials_394 = {'Aluminum 1Kg': 0.167, 'Copper 1Kg': 0, 'Gold 1Kg': 0.41, 'Silver 1Kg': 0.436, 'Ham_Petrol_Fiyati 1L': 0.398, 'Elektrik_Ucreti 1kW': 0.073, 'Asgari_Ucret 1 iş günü': 0.313, 'Dogal_Gaz 100m^3': 0.301, 'USD': 0.081, 'EUR': 0}
# insert_daily_costs("Product 394", product_materials_394)
#
# product_materials_395 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.14, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.398, 'Dogal_Gaz 100m^3': 0, 'USD': 0.268, 'EUR': 0.392}
# insert_daily_costs("Product 395", product_materials_395)
#
# product_materials_396 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.123, 'Gold 1Kg': 0.156, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.008, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 396", product_materials_396)
#
# product_materials_397 = {'Aluminum 1Kg': 0.496, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.426, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.481, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 397", product_materials_397)
#
# product_materials_398 = {'Aluminum 1Kg': 0.097, 'Copper 1Kg': 0.432, 'Gold 1Kg': 0.472, 'Silver 1Kg': 0.368, 'Ham_Petrol_Fiyati 1L': 0.187, 'Elektrik_Ucreti 1kW': 0.117, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.242, 'EUR': 0}
# insert_daily_costs("Product 398", product_materials_398)
#
# product_materials_399 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.314, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.121, 'Elektrik_Ucreti 1kW': 0.019, 'Asgari_Ucret 1 iş günü': 0.35, 'Dogal_Gaz 100m^3': 0, 'USD': 0.104, 'EUR': 0}
# insert_daily_costs("Product 399", product_materials_399)
#
# product_materials_400 = {'Aluminum 1Kg': 0.174, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.307, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.474, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.118, 'EUR': 0.089}
# insert_daily_costs("Product 400", product_materials_400)
#
# product_materials_401 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.383, 'Gold 1Kg': 0, 'Silver 1Kg': 0.304, 'Ham_Petrol_Fiyati 1L': 0.069, 'Elektrik_Ucreti 1kW': 0.373, 'Asgari_Ucret 1 iş günü': 0.093, 'Dogal_Gaz 100m^3': 0, 'USD': 0.447, 'EUR': 0.239}
# insert_daily_costs("Product 401", product_materials_401)
#
# product_materials_402 = {'Aluminum 1Kg': 0.36, 'Copper 1Kg': 0.348, 'Gold 1Kg': 0.02, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.33, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.042, 'USD': 0, 'EUR': 0.196}
# insert_daily_costs("Product 402", product_materials_402)
#
# product_materials_403 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.227, 'Gold 1Kg': 0.353, 'Silver 1Kg': 0.053, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.337, 'EUR': 0.296}
# insert_daily_costs("Product 403", product_materials_403)
#
# product_materials_404 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.007, 'Gold 1Kg': 0.25, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.32, 'Elektrik_Ucreti 1kW': 0.187, 'Asgari_Ucret 1 iş günü': 0.11, 'Dogal_Gaz 100m^3': 0, 'USD': 0.214, 'EUR': 0.239}
# insert_daily_costs("Product 404", product_materials_404)
#
# product_materials_405 = {'Aluminum 1Kg': 0.227, 'Copper 1Kg': 0.046, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.178, 'Elektrik_Ucreti 1kW': 0.02, 'Asgari_Ucret 1 iş günü': 0.188, 'Dogal_Gaz 100m^3': 0.189, 'USD': 0, 'EUR': 0.303}
# insert_daily_costs("Product 405", product_materials_405)
#
# product_materials_406 = {'Aluminum 1Kg': 0.246, 'Copper 1Kg': 0.367, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.206, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.354, 'Dogal_Gaz 100m^3': 0, 'USD': 0.481, 'EUR': 0}
# insert_daily_costs("Product 406", product_materials_406)
#
# product_materials_407 = {'Aluminum 1Kg': 0.034, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.327, 'Ham_Petrol_Fiyati 1L': 0.075, 'Elektrik_Ucreti 1kW': 0.485, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.451}
# insert_daily_costs("Product 407", product_materials_407)
#
# product_materials_408 = {'Aluminum 1Kg': 0.295, 'Copper 1Kg': 0.363, 'Gold 1Kg': 0.382, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.23, 'Elektrik_Ucreti 1kW': 0.336, 'Asgari_Ucret 1 iş günü': 0.176, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 408", product_materials_408)
#
# product_materials_409 = {'Aluminum 1Kg': 0.117, 'Copper 1Kg': 0, 'Gold 1Kg': 0.262, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.203, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.436, 'USD': 0, 'EUR': 0.126}
# insert_daily_costs("Product 409", product_materials_409)
#
# product_materials_410 = {'Aluminum 1Kg': 0.345, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.005, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.425, 'EUR': 0}
# insert_daily_costs("Product 410", product_materials_410)
#
# product_materials_411 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.147, 'Gold 1Kg': 0.06, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.176, 'Dogal_Gaz 100m^3': 0.349, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 411", product_materials_411)
#
# product_materials_412 = {'Aluminum 1Kg': 0.348, 'Copper 1Kg': 0.372, 'Gold 1Kg': 0.157, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.177, 'Elektrik_Ucreti 1kW': 0.38, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.061, 'USD': 0.268, 'EUR': 0}
# insert_daily_costs("Product 412", product_materials_412)
#
# product_materials_413 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.048, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.164}
# insert_daily_costs("Product 413", product_materials_413)
#
# product_materials_414 = {'Aluminum 1Kg': 0.207, 'Copper 1Kg': 0.479, 'Gold 1Kg': 0.088, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.239, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 414", product_materials_414)
#
# product_materials_415 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.288, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.487, 'Asgari_Ucret 1 iş günü': 0.317, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.085}
# insert_daily_costs("Product 415", product_materials_415)
#
# product_materials_416 = {'Aluminum 1Kg': 0.008, 'Copper 1Kg': 0.4, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.327, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.423}
# insert_daily_costs("Product 416", product_materials_416)
#
# product_materials_417 = {'Aluminum 1Kg': 0.181, 'Copper 1Kg': 0, 'Gold 1Kg': 0.094, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.163, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 417", product_materials_417)
#
# product_materials_418 = {'Aluminum 1Kg': 0.396, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.347, 'Ham_Petrol_Fiyati 1L': 0.366, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.491, 'Dogal_Gaz 100m^3': 0, 'USD': 0.486, 'EUR': 0.082}
# insert_daily_costs("Product 418", product_materials_418)
#
# product_materials_419 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.282, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.329, 'USD': 0, 'EUR': 0.339}
# insert_daily_costs("Product 419", product_materials_419)
#
# product_materials_420 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.024, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.341, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 420", product_materials_420)
#
# product_materials_421 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.385, 'Gold 1Kg': 0.006, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.347, 'USD': 0, 'EUR': 0.469}
# insert_daily_costs("Product 421", product_materials_421)
#
# product_materials_422 = {'Aluminum 1Kg': 0.347, 'Copper 1Kg': 0, 'Gold 1Kg': 0.164, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.367, 'Asgari_Ucret 1 iş günü': 0.313, 'Dogal_Gaz 100m^3': 0.309, 'USD': 0.474, 'EUR': 0}
# insert_daily_costs("Product 422", product_materials_422)
#
# product_materials_423 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.123, 'Silver 1Kg': 0.146, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.492, 'Asgari_Ucret 1 iş günü': 0.284, 'Dogal_Gaz 100m^3': 0, 'USD': 0.266, 'EUR': 0}
# insert_daily_costs("Product 423", product_materials_423)
#
# product_materials_424 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.153, 'Gold 1Kg': 0, 'Silver 1Kg': 0.296, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.431, 'Asgari_Ucret 1 iş günü': 0.336, 'Dogal_Gaz 100m^3': 0, 'USD': 0.391, 'EUR': 0}
# insert_daily_costs("Product 424", product_materials_424)
#
# product_materials_425 = {'Aluminum 1Kg': 0.058, 'Copper 1Kg': 0.373, 'Gold 1Kg': 0.085, 'Silver 1Kg': 0.073, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.124, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.252, 'EUR': 0.437}
# insert_daily_costs("Product 425", product_materials_425)
#
# product_materials_426 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.245, 'Gold 1Kg': 0.483, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.223, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.336}
# insert_daily_costs("Product 426", product_materials_426)
#
# product_materials_427 = {'Aluminum 1Kg': 0.179, 'Copper 1Kg': 0, 'Gold 1Kg': 0.418, 'Silver 1Kg': 0.497, 'Ham_Petrol_Fiyati 1L': 0.482, 'Elektrik_Ucreti 1kW': 0.322, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.37, 'EUR': 0}
# insert_daily_costs("Product 427", product_materials_427)
#
# product_materials_428 = {'Aluminum 1Kg': 0.038, 'Copper 1Kg': 0.116, 'Gold 1Kg': 0.084, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.348, 'Dogal_Gaz 100m^3': 0, 'USD': 0.418, 'EUR': 0}
# insert_daily_costs("Product 428", product_materials_428)
#
# product_materials_429 = {'Aluminum 1Kg': 0.471, 'Copper 1Kg': 0, 'Gold 1Kg': 0.105, 'Silver 1Kg': 0.079, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.155, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 429", product_materials_429)
#
# product_materials_430 = {'Aluminum 1Kg': 0.269, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.293, 'Ham_Petrol_Fiyati 1L': 0.229, 'Elektrik_Ucreti 1kW': 0.053, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.459, 'USD': 0, 'EUR': 0.39}
# insert_daily_costs("Product 430", product_materials_430)
#
# product_materials_431 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.006, 'Silver 1Kg': 0.373, 'Ham_Petrol_Fiyati 1L': 0.114, 'Elektrik_Ucreti 1kW': 0.075, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.454, 'EUR': 0}
# insert_daily_costs("Product 431", product_materials_431)
#
# product_materials_432 = {'Aluminum 1Kg': 0.392, 'Copper 1Kg': 0.479, 'Gold 1Kg': 0.314, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.213, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.131, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 432", product_materials_432)
#
# product_materials_433 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.425, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.199, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.084, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 433", product_materials_433)
#
# product_materials_434 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.391, 'Silver 1Kg': 0.497, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.498}
# insert_daily_costs("Product 434", product_materials_434)
#
# product_materials_435 = {'Aluminum 1Kg': 0.248, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.46, 'Ham_Petrol_Fiyati 1L': 0.103, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.286, 'Dogal_Gaz 100m^3': 0.494, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 435", product_materials_435)
#
# product_materials_436 = {'Aluminum 1Kg': 0.339, 'Copper 1Kg': 0.222, 'Gold 1Kg': 0, 'Silver 1Kg': 0.28, 'Ham_Petrol_Fiyati 1L': 0.458, 'Elektrik_Ucreti 1kW': 0.471, 'Asgari_Ucret 1 iş günü': 0.008, 'Dogal_Gaz 100m^3': 0.101, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 436", product_materials_436)
#
# product_materials_437 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.114, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.258, 'Asgari_Ucret 1 iş günü': 0.442, 'Dogal_Gaz 100m^3': 0.357, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 437", product_materials_437)
#
# product_materials_438 = {'Aluminum 1Kg': 0.302, 'Copper 1Kg': 0.494, 'Gold 1Kg': 0.07, 'Silver 1Kg': 0.168, 'Ham_Petrol_Fiyati 1L': 0.113, 'Elektrik_Ucreti 1kW': 0.015, 'Asgari_Ucret 1 iş günü': 0.242, 'Dogal_Gaz 100m^3': 0, 'USD': 0.494, 'EUR': 0}
# insert_daily_costs("Product 438", product_materials_438)
#
# product_materials_439 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.314, 'Gold 1Kg': 0.385, 'Silver 1Kg': 0.019, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.466, 'Asgari_Ucret 1 iş günü': 0.386, 'Dogal_Gaz 100m^3': 0, 'USD': 0.484, 'EUR': 0.349}
# insert_daily_costs("Product 439", product_materials_439)
#
# product_materials_440 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.103, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 440", product_materials_440)
#
# product_materials_441 = {'Aluminum 1Kg': 0.457, 'Copper 1Kg': 0, 'Gold 1Kg': 0.493, 'Silver 1Kg': 0.403, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.38, 'Asgari_Ucret 1 iş günü': 0.471, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 441", product_materials_441)
#
# product_materials_442 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.341, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.155, 'EUR': 0}
# insert_daily_costs("Product 442", product_materials_442)
#
# product_materials_443 = {'Aluminum 1Kg': 0.457, 'Copper 1Kg': 0.031, 'Gold 1Kg': 0.066, 'Silver 1Kg': 0.05, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.438, 'Asgari_Ucret 1 iş günü': 0.181, 'Dogal_Gaz 100m^3': 0.25, 'USD': 0, 'EUR': 0.381}
# insert_daily_costs("Product 443", product_materials_443)
#
# product_materials_444 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.288, 'Silver 1Kg': 0.341, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.123, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.391, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 444", product_materials_444)
#
# product_materials_445 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.348, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.11, 'Elektrik_Ucreti 1kW': 0.408, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.067, 'EUR': 0}
# insert_daily_costs("Product 445", product_materials_445)
#
# product_materials_446 = {'Aluminum 1Kg': 0.026, 'Copper 1Kg': 0, 'Gold 1Kg': 0.12, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.183, 'USD': 0.142, 'EUR': 0}
# insert_daily_costs("Product 446", product_materials_446)
#
# product_materials_447 = {'Aluminum 1Kg': 0.423, 'Copper 1Kg': 0.291, 'Gold 1Kg': 0.068, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.414, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.099, 'EUR': 0}
# insert_daily_costs("Product 447", product_materials_447)
#
# product_materials_448 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.309, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.461, 'USD': 0.241, 'EUR': 0.191}
# insert_daily_costs("Product 448", product_materials_448)
#
# product_materials_449 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.184, 'Silver 1Kg': 0.117, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.193}
# insert_daily_costs("Product 449", product_materials_449)
#
# product_materials_450 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.164, 'Gold 1Kg': 0, 'Silver 1Kg': 0.163, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 450", product_materials_450)
#
# product_materials_451 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.32, 'Elektrik_Ucreti 1kW': 0.431, 'Asgari_Ucret 1 iş günü': 0.01, 'Dogal_Gaz 100m^3': 0.188, 'USD': 0.04, 'EUR': 0.103}
# insert_daily_costs("Product 451", product_materials_451)
#
# product_materials_452 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.175, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.204, 'Elektrik_Ucreti 1kW': 0.261, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 452", product_materials_452)
#
# product_materials_453 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.235, 'Silver 1Kg': 0.486, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.21, 'USD': 0.254, 'EUR': 0}
# insert_daily_costs("Product 453", product_materials_453)
#
# product_materials_454 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.307, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.224, 'Elektrik_Ucreti 1kW': 0.374, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.051, 'USD': 0.115, 'EUR': 0}
# insert_daily_costs("Product 454", product_materials_454)
#
# product_materials_455 = {'Aluminum 1Kg': 0.096, 'Copper 1Kg': 0, 'Gold 1Kg': 0.309, 'Silver 1Kg': 0.043, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.065, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 455", product_materials_455)
#
# product_materials_456 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.013, 'Gold 1Kg': 0.497, 'Silver 1Kg': 0.093, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.422, 'Asgari_Ucret 1 iş günü': 0.204, 'Dogal_Gaz 100m^3': 0.208, 'USD': 0, 'EUR': 0.252}
# insert_daily_costs("Product 456", product_materials_456)
#
# product_materials_457 = {'Aluminum 1Kg': 0.248, 'Copper 1Kg': 0.38, 'Gold 1Kg': 0, 'Silver 1Kg': 0.49, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.296, 'EUR': 0.4}
# insert_daily_costs("Product 457", product_materials_457)
#
# product_materials_458 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.117, 'Gold 1Kg': 0, 'Silver 1Kg': 0.326, 'Ham_Petrol_Fiyati 1L': 0.426, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.381, 'Dogal_Gaz 100m^3': 0.378, 'USD': 0.208, 'EUR': 0.081}
# insert_daily_costs("Product 458", product_materials_458)
#
# product_materials_459 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.012, 'Ham_Petrol_Fiyati 1L': 0.31, 'Elektrik_Ucreti 1kW': 0.392, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.327, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 459", product_materials_459)
#
# product_materials_460 = {'Aluminum 1Kg': 0.167, 'Copper 1Kg': 0.399, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.174, 'Elektrik_Ucreti 1kW': 0.464, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 460", product_materials_460)
#
# product_materials_461 = {'Aluminum 1Kg': 0.067, 'Copper 1Kg': 0, 'Gold 1Kg': 0.5, 'Silver 1Kg': 0.463, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.196, 'Dogal_Gaz 100m^3': 0.122, 'USD': 0, 'EUR': 0.431}
# insert_daily_costs("Product 461", product_materials_461)
#
# product_materials_462 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.005, 'Gold 1Kg': 0.228, 'Silver 1Kg': 0.312, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.243, 'Dogal_Gaz 100m^3': 0.164, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 462", product_materials_462)
#
# product_materials_463 = {'Aluminum 1Kg': 0.33, 'Copper 1Kg': 0.425, 'Gold 1Kg': 0, 'Silver 1Kg': 0.432, 'Ham_Petrol_Fiyati 1L': 0.256, 'Elektrik_Ucreti 1kW': 0.175, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.394, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 463", product_materials_463)
#
# product_materials_464 = {'Aluminum 1Kg': 0.319, 'Copper 1Kg': 0.161, 'Gold 1Kg': 0, 'Silver 1Kg': 0.146, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.468, 'USD': 0.063, 'EUR': 0.432}
# insert_daily_costs("Product 464", product_materials_464)
#
# product_materials_465 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.132, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.466, 'EUR': 0}
# insert_daily_costs("Product 465", product_materials_465)
#
# product_materials_466 = {'Aluminum 1Kg': 0.323, 'Copper 1Kg': 0, 'Gold 1Kg': 0.468, 'Silver 1Kg': 0.205, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.14, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.202, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 466", product_materials_466)
#
# product_materials_467 = {'Aluminum 1Kg': 0.457, 'Copper 1Kg': 0.397, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.082, 'Elektrik_Ucreti 1kW': 0.172, 'Asgari_Ucret 1 iş günü': 0.443, 'Dogal_Gaz 100m^3': 0.301, 'USD': 0.431, 'EUR': 0}
# insert_daily_costs("Product 467", product_materials_467)
#
# product_materials_468 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.492, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.426, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.382, 'USD': 0.101, 'EUR': 0.201}
# insert_daily_costs("Product 468", product_materials_468)
#
# product_materials_469 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.221, 'Silver 1Kg': 0.008, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.423, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 469", product_materials_469)
#
# product_materials_470 = {'Aluminum 1Kg': 0.412, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.256, 'Ham_Petrol_Fiyati 1L': 0.472, 'Elektrik_Ucreti 1kW': 0.246, 'Asgari_Ucret 1 iş günü': 0.253, 'Dogal_Gaz 100m^3': 0.437, 'USD': 0, 'EUR': 0.024}
# insert_daily_costs("Product 470", product_materials_470)
#
# product_materials_471 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.012, 'Asgari_Ucret 1 iş günü': 0.274, 'Dogal_Gaz 100m^3': 0.167, 'USD': 0.412, 'EUR': 0.239}
# insert_daily_costs("Product 471", product_materials_471)
#
# product_materials_472 = {'Aluminum 1Kg': 0.385, 'Copper 1Kg': 0.324, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.407, 'Elektrik_Ucreti 1kW': 0.319, 'Asgari_Ucret 1 iş günü': 0.233, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.12}
# insert_daily_costs("Product 472", product_materials_472)
#
# product_materials_473 = {'Aluminum 1Kg': 0.191, 'Copper 1Kg': 0.023, 'Gold 1Kg': 0.393, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.433, 'Dogal_Gaz 100m^3': 0, 'USD': 0.384, 'EUR': 0.467}
# insert_daily_costs("Product 473", product_materials_473)
#
# product_materials_474 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.116, 'Gold 1Kg': 0.167, 'Silver 1Kg': 0.487, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.499, 'Asgari_Ucret 1 iş günü': 0.255, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 474", product_materials_474)
#
# product_materials_475 = {'Aluminum 1Kg': 0.418, 'Copper 1Kg': 0.215, 'Gold 1Kg': 0, 'Silver 1Kg': 0.191, 'Ham_Petrol_Fiyati 1L': 0.039, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.045, 'Dogal_Gaz 100m^3': 0.422, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 475", product_materials_475)
#
# product_materials_476 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.436, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.192, 'Elektrik_Ucreti 1kW': 0.465, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.419, 'EUR': 0}
# insert_daily_costs("Product 476", product_materials_476)
#
# product_materials_477 = {'Aluminum 1Kg': 0.237, 'Copper 1Kg': 0, 'Gold 1Kg': 0.343, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.265, 'Dogal_Gaz 100m^3': 0.294, 'USD': 0.455, 'EUR': 0.439}
# insert_daily_costs("Product 477", product_materials_477)
#
# product_materials_478 = {'Aluminum 1Kg': 0.327, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.026, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.222, 'Asgari_Ucret 1 iş günü': 0.082, 'Dogal_Gaz 100m^3': 0.365, 'USD': 0, 'EUR': 0.285}
# insert_daily_costs("Product 478", product_materials_478)
#
# product_materials_479 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.113, 'Gold 1Kg': 0.278, 'Silver 1Kg': 0.271, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.241, 'Asgari_Ucret 1 iş günü': 0.478, 'Dogal_Gaz 100m^3': 0, 'USD': 0.006, 'EUR': 0}
# insert_daily_costs("Product 479", product_materials_479)
#
# product_materials_480 = {'Aluminum 1Kg': 0.251, 'Copper 1Kg': 0, 'Gold 1Kg': 0.025, 'Silver 1Kg': 0.09, 'Ham_Petrol_Fiyati 1L': 0.189, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.094, 'USD': 0.384, 'EUR': 0}
# insert_daily_costs("Product 480", product_materials_480)
#
# product_materials_481 = {'Aluminum 1Kg': 0.405, 'Copper 1Kg': 0.117, 'Gold 1Kg': 0, 'Silver 1Kg': 0.252, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.377, 'USD': 0.5, 'EUR': 0}
# insert_daily_costs("Product 481", product_materials_481)
#
# product_materials_482 = {'Aluminum 1Kg': 0.312, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.296, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.085, 'Asgari_Ucret 1 iş günü': 0.326, 'Dogal_Gaz 100m^3': 0, 'USD': 0.311, 'EUR': 0.233}
# insert_daily_costs("Product 482", product_materials_482)
#
# product_materials_483 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0.195, 'Silver 1Kg': 0.248, 'Ham_Petrol_Fiyati 1L': 0.256, 'Elektrik_Ucreti 1kW': 0.288, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.395, 'EUR': 0}
# insert_daily_costs("Product 483", product_materials_483)
#
# product_materials_484 = {'Aluminum 1Kg': 0.212, 'Copper 1Kg': 0.094, 'Gold 1Kg': 0.202, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.468, 'Elektrik_Ucreti 1kW': 0.438, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.239, 'USD': 0.212, 'EUR': 0.494}
# insert_daily_costs("Product 484", product_materials_484)
#
# product_materials_485 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.494, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.083, 'Dogal_Gaz 100m^3': 0.349, 'USD': 0, 'EUR': 0.082}
# insert_daily_costs("Product 485", product_materials_485)
#
# product_materials_486 = {'Aluminum 1Kg': 0.382, 'Copper 1Kg': 0.42, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.403, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.301}
# insert_daily_costs("Product 486", product_materials_486)
#
# product_materials_487 = {'Aluminum 1Kg': 0.05, 'Copper 1Kg': 0, 'Gold 1Kg': 0.39, 'Silver 1Kg': 0.358, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.328, 'Asgari_Ucret 1 iş günü': 0.343, 'Dogal_Gaz 100m^3': 0.23, 'USD': 0, 'EUR': 0.374}
# insert_daily_costs("Product 487", product_materials_487)
#
# product_materials_488 = {'Aluminum 1Kg': 0.007, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.057, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0.381}
# insert_daily_costs("Product 488", product_materials_488)
#
# product_materials_489 = {'Aluminum 1Kg': 0.126, 'Copper 1Kg': 0.411, 'Gold 1Kg': 0, 'Silver 1Kg': 0.033, 'Ham_Petrol_Fiyati 1L': 0.429, 'Elektrik_Ucreti 1kW': 0.096, 'Asgari_Ucret 1 iş günü': 0.255, 'Dogal_Gaz 100m^3': 0.135, 'USD': 0, 'EUR': 0.389}
# insert_daily_costs("Product 489", product_materials_489)
#
# product_materials_490 = {'Aluminum 1Kg': 0.281, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0.343, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 490", product_materials_490)
#
# product_materials_491 = {'Aluminum 1Kg': 0.39, 'Copper 1Kg': 0.177, 'Gold 1Kg': 0.082, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.289, 'Asgari_Ucret 1 iş günü': 0.027, 'Dogal_Gaz 100m^3': 0, 'USD': 0.376, 'EUR': 0.261}
# insert_daily_costs("Product 491", product_materials_491)
#
# product_materials_492 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.224, 'Gold 1Kg': 0, 'Silver 1Kg': 0.115, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.33, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.269, 'EUR': 0}
# insert_daily_costs("Product 492", product_materials_492)
#
# product_materials_493 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.429, 'Gold 1Kg': 0.423, 'Silver 1Kg': 0.021, 'Ham_Petrol_Fiyati 1L': 0.03, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.056, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 493", product_materials_493)
#
# product_materials_494 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.056, 'Gold 1Kg': 0.197, 'Silver 1Kg': 0.014, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.219, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0.289, 'USD': 0, 'EUR': 0.459}
# insert_daily_costs("Product 494", product_materials_494)
#
# product_materials_495 = {'Aluminum 1Kg': 0.293, 'Copper 1Kg': 0.313, 'Gold 1Kg': 0, 'Silver 1Kg': 0.047, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.406, 'Dogal_Gaz 100m^3': 0.206, 'USD': 0, 'EUR': 0.291}
# insert_daily_costs("Product 495", product_materials_495)
#
# product_materials_496 = {'Aluminum 1Kg': 0.375, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.45, 'Asgari_Ucret 1 iş günü': 0.361, 'Dogal_Gaz 100m^3': 0, 'USD': 0.373, 'EUR': 0}
# insert_daily_costs("Product 496", product_materials_496)
#
# product_materials_497 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.355, 'Gold 1Kg': 0.216, 'Silver 1Kg': 0.365, 'Ham_Petrol_Fiyati 1L': 0, 'Elektrik_Ucreti 1kW': 0.299, 'Asgari_Ucret 1 iş günü': 0.493, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 497", product_materials_497)
#
# product_materials_498 = {'Aluminum 1Kg': 0.29, 'Copper 1Kg': 0.345, 'Gold 1Kg': 0.103, 'Silver 1Kg': 0.201, 'Ham_Petrol_Fiyati 1L': 0.222, 'Elektrik_Ucreti 1kW': 0.122, 'Asgari_Ucret 1 iş günü': 0, 'Dogal_Gaz 100m^3': 0, 'USD': 0.31, 'EUR': 0}
# insert_daily_costs("Product 498", product_materials_498)
#
# product_materials_499 = {'Aluminum 1Kg': 0, 'Copper 1Kg': 0.389, 'Gold 1Kg': 0.116, 'Silver 1Kg': 0.334, 'Ham_Petrol_Fiyati 1L': 0.063, 'Elektrik_Ucreti 1kW': 0, 'Asgari_Ucret 1 iş günü': 0.492, 'Dogal_Gaz 100m^3': 0, 'USD': 0.024, 'EUR': 0}
# insert_daily_costs("Product 499", product_materials_499)
#
# product_materials_500 = {'Aluminum 1Kg': 0.035, 'Copper 1Kg': 0, 'Gold 1Kg': 0, 'Silver 1Kg': 0.026, 'Ham_Petrol_Fiyati 1L': 0.057, 'Elektrik_Ucreti 1kW': 0.206, 'Asgari_Ucret 1 iş günü': 0.456, 'Dogal_Gaz 100m^3': 0, 'USD': 0, 'EUR': 0}
# insert_daily_costs("Product 500", product_materials_500)