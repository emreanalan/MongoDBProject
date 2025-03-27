import pymongo
import pandas as pd
from datetime import datetime, timedelta

# MongoDB connection
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["Final_Project"]

collections = {
    "Aluminum": db["Aluminum/TRY"],
    "Copper": db["Copper/TRY"],
    "Gold": db["Gold/TRY"],
    "Silver": db["Silver/TRY"],
    "USD_TRY": db["USD/TRY"],
    "EUR_TRY": db["EUR/TRY"],
    "Elektrik_Ucreti": db["Elektrik_Ucreti"],
    "Asgari_Ucret": db["Asgari_Ucret"],
    "DogalGaz_Ucreti": db["DogalGaz_Ucreti"],
    "Ham_Petrol_Fiyati": db["Ham_Petrol_Fiyati"],

}


# Helper functions
def clean_price(price_str):
    """Cleans the price string and converts it to a float."""
    if isinstance(price_str, str):
        price_str = price_str.replace(" TL", "").replace(",", ".")
        if price_str.count(".") > 1:
            price_str = price_str.replace(".", "", price_str.count(".") - 1)
        try:
            return float(price_str)
        except ValueError as e:
            print(f"Error converting price '{price_str}' to float: {e}")
            return None
    return None


def fetch_data(collection_name, price_column="Price"):
    collection = collections[collection_name]
    cursor = collection.find({}, {"Date": 1, price_column: 1}).sort("Date", pymongo.ASCENDING)
    data = pd.DataFrame(list(cursor))
    data["Date"] = pd.to_datetime(data["Date"]).dt.date
    data[price_column] = data[price_column].apply(clean_price)
    return data


def fetch_electricity_price(date):
    collection = collections["Elektrik_Ucreti"]
    if date.year == 2023:
        price_record = collection.find_one({"Date": datetime(2023, 1, 1)})
    else:
        price_record = collection.find_one({"Date": datetime(2024, 1, 1)})
    if price_record:
        return clean_price(price_record["Price"])
    return None


def fetch_asgari_ucret_price(date):
    collection = collections["Asgari_Ucret"]
    if date < datetime(2023, 7, 1).date():
        price_record = collection.find_one({"Date": datetime(2023, 1, 1)})
    elif date < datetime(2024, 1, 1).date():
        price_record = collection.find_one({"Date": datetime(2023, 7, 1)})
    else:
        price_record = collection.find_one({"Date": datetime(2024, 1, 1)})
    if price_record:
        return clean_price(price_record["Price"])
    return None


def fetch_dogalgaz_price(date):
    collection = collections["DogalGaz_Ucreti"]
    if date < datetime(2024, 1, 1).date():
        price_record = collection.find_one({"Date": datetime(2023, 1, 1)})
    else:
        price_record = collection.find_one({"Date": datetime(2024, 1, 1)})
    if price_record:
        return clean_price(price_record["Price"])
    return None


def get_latest_price(data, date, price_column="Price"):
    recent_data = data[data["Date"] <= date]
    if not recent_data.empty:
        return recent_data.iloc[-1][price_column]
    return None


def get_last_recorded_date(product_name):
    product_collection = db[product_name]
    last_record = product_collection.find_one(sort=[("Date", pymongo.DESCENDING)])
    if last_record:
        return last_record["Date"].date()  # Convert to date
    return None


def calculate_daily_costs(product_name, materials, start_date):
    gold_data = fetch_data("Gold")
    copper_data = fetch_data("Copper")
    aluminum_data = fetch_data("Aluminum")
    silver_data = fetch_data("Silver")
    usd_try_data = fetch_data("USD_TRY")
    eur_try_data = fetch_data("EUR_TRY")
    ham_petrol_data = fetch_data("Ham_Petrol_Fiyati")

    daily_costs = []

    for date in pd.date_range(start=start_date, end=datetime.now(), freq="D").date:
        gold_cost = get_latest_price(gold_data, date)
        copper_cost = get_latest_price(copper_data, date)
        aluminum_cost = get_latest_price(aluminum_data, date)
        silver_cost = get_latest_price(silver_data, date)
        ham_petrol_cost = get_latest_price(ham_petrol_data, date)
        usd_to_try = get_latest_price(usd_try_data, date)
        eur_to_try = get_latest_price(eur_try_data, date)
        electricity_cost = fetch_electricity_price(date)
        asgari_ucret_cost = fetch_asgari_ucret_price(date)
        dogalgaz_cost = fetch_dogalgaz_price(date)

        if all(
                value is not None
                for value in [
                    gold_cost,
                    copper_cost,
                    aluminum_cost,
                    silver_cost,
                    usd_to_try,
                    eur_to_try,
                    electricity_cost,
                    asgari_ucret_cost,
                    dogalgaz_cost,
                    ham_petrol_cost,
                ]
        ):
            aluminum_cost_per_day = float(aluminum_cost * materials.get("Aluminum 1Kg", 0))
            gold_cost_per_day = float(gold_cost * materials.get("Gold 1Kg", 0))
            copper_cost_per_day = float(copper_cost * materials.get("Copper 1Kg", 0))
            silver_cost_per_day = float(silver_cost * materials.get("Silver 1Kg", 0))
            hampetrol_cost_per_day = float(ham_petrol_cost * materials.get("Ham_Petrol_Fiyati 1L", 0))
            electricity_cost_per_day = float(electricity_cost * materials.get("Elektrik_Ucreti 1kW", 0))
            asgari_ucret_cost_per_day = float((asgari_ucret_cost / 30) * materials.get("Asgari_Ucret 1 iş günü", 0))
            dogalgaz_cost_per_day = float(dogalgaz_cost * materials.get("Dogal_Gaz 100m^3", 0))
            other_expenses = float(usd_to_try * materials.get("USD", 0))
            other_expenses_euro = float(eur_to_try * materials.get("EUR", 0))

            # print(f"Gold cost on {date}: {gold_cost} and {materials.get('Gold', 0)}")
            # print(f"Copper cost on {date}: {copper_cost}")
            # print(f"Aluminum cost on {date}: {aluminum_cost}")
            # print(f"Electricity cost on {date}: {electricity_cost}")
            # print(f"hampetrol cost on {date}: {ham_petrol_cost}")
            # print(f"other1 cost on {date}: {other_expenses}")
            # print(f"other2 cost on {date}: {other_expenses_euro}")
            # print(f"{aluminum_cost_per_day} + {gold_cost_per_day} + {copper_cost_per_day} + {silver_cost_per_day} + {other_expenses} + {asgari_ucret_cost_per_day} + {dogalgaz_cost_per_day} + {hampetrol_cost_per_day} + {other_expenses_euro} + {electricity_cost_per_day}")

            total_cost = (
                    aluminum_cost_per_day
                    + gold_cost_per_day
                    + copper_cost_per_day
                    + silver_cost_per_day
                    + other_expenses
                    + asgari_ucret_cost_per_day
                    + dogalgaz_cost_per_day
                    + hampetrol_cost_per_day
                    + other_expenses_euro
                    + electricity_cost_per_day
            )
            total_cost = round(total_cost, 2)
            total_cost_str = f"{total_cost:,.2f} TL"

            materials_str = ", ".join([f"{value} {key}" for key, value in materials.items() if value > 0])

            daily_costs.append(
                {
                    "Date": datetime.combine(date, datetime.min.time()),  # Convert to datetime
                    "Cost": total_cost_str,
                    "Materials": materials_str,
                    "Description": f"{date.day}/{date.month}/{date.year} cost of this {product_name}",
                }
            )

    return daily_costs


def insert_daily_costs(product_name, materials):
    last_date = get_last_recorded_date(product_name)
    if last_date:
        start_date = last_date + timedelta(days=1)  # Start from the next day
    else:
        start_date = datetime(2023, 1, 1).date()  # Default start date if no records exist

    daily_costs = calculate_daily_costs(product_name, materials, start_date)

    if not daily_costs:
        print(f"No new data inserted for '{product_name}'. Record is up-to-date.")
        return

    product_collection = db[product_name]

    for record in daily_costs:
        product_collection.insert_one(record)
        print(f"Record inserted: Date: {record['Date']}, Cost: {record['Cost']}")

    print(f"Inserted {len(daily_costs)} new records for '{product_name}'.")


copperCable_materials = {
    "Aluminum 1Kg": 0,
    "Copper 1Kg": 0.05,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1,
}
GoldCable_materials = {
    "Aluminum 1Kg": 0,
    "Copper 1Kg": 0.01,
    "Gold 1Kg": 0.005,
    "Silver 1Kg": 0,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1,
}
USBCable_materials = {
    "Aluminum 1Kg": 0.01,
    "Copper 1Kg": 0.03,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1
}
silverCable_materials = {
    "Aluminum 1Kg": 0.01,
    "Copper 1Kg": 0,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 0,
    "EUR": 1
}
toy_Car_materials = {
    "Aluminum 1Kg": 0.01,
    "Copper 1Kg": 0.001,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 0,
    "EUR": 1
}
toy_AliminumGun_materials = {
    "Aluminum 1Kg": 0.03,
    "Copper 1Kg": 0,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 0,
    "EUR": 2
}
toy_TeddyBear_materials = {
    "Aluminum 1Kg": 0.01,
    "Copper 1Kg": 0.001,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 30,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.1,
    "USD": 10,
    "EUR": 0
}
gamePad_materials = {
    "Aluminum 1Kg": 0.01,
    "Copper 1Kg": 0.001,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.001,
    "Ham_Petrol_Fiyati 1L": 10,
    "Elektrik_Ucreti 1kW": 100,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 5,
    "EUR": 0
}
headphones_materials = {
    "Aluminum 1Kg": 0.05,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 0.5,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1
}
laptop_materials = {
    "Aluminum 1Kg": 0.5,
    "Copper 1Kg": 0.3,
    "Gold 1Kg": 0.01,
    "Silver 1Kg": 0.05,
    "Ham_Petrol_Fiyati 1L": 0.8,
    "Elektrik_Ucreti 1kW": 3,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.02,
    "USD": 1,
    "EUR": 1
}
smartphone_materials = {
    "Aluminum 1Kg": 0.3,
    "Copper 1Kg": 0.2,
    "Gold 1Kg": 0.05,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 1,
    "Elektrik_Ucreti 1kW": 2,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.015,
    "USD": 1,
    "EUR": 1
}
tablet_materials = {
    "Aluminum 1Kg": 0.4,
    "Copper 1Kg": 0.25,
    "Gold 1Kg": 0.03,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 0.6,
    "Elektrik_Ucreti 1kW": 2,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1
}
smartwatch_materials = {
    "Aluminum 1Kg": 0.1,
    "Copper 1Kg": 0.05,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.01,
    "Ham_Petrol_Fiyati 1L": 0.5,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1
}
gamingMouse_materials = {
    "Aluminum 1Kg": 0.05,
    "Copper 1Kg": 0.02,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.01,
    "Ham_Petrol_Fiyati 1L": 0.3,
    "Elektrik_Ucreti 1kW": 0.5,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.005,
    "USD": 0.8,
    "EUR": 0.9
}
electricFan_materials = {
    "Aluminum 1Kg": 0.1,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.01,
    "Ham_Petrol_Fiyati 1L": 0.7,
    "Elektrik_Ucreti 1kW": 0.6,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.02,
    "USD": 1,
    "EUR": 1
}
microwave_materials = {
    "Aluminum 1Kg": 0.2,
    "Copper 1Kg": 0.15,
    "Gold 1Kg": 0.02,
    "Silver 1Kg": 0.05,
    "Ham_Petrol_Fiyati 1L": 0.9,
    "Elektrik_Ucreti 1kW": 1.5,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1
}
vacuumCleaner_materials = {
    "Aluminum 1Kg": 0.25,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 0.6,
    "Elektrik_Ucreti 1kW": 1.2,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.015,
    "USD": 0.9,
    "EUR": 1
}
airConditioner_materials = {
    "Aluminum 1Kg": 0.5,
    "Copper 1Kg": 0.3,
    "Gold 1Kg": 0.05,
    "Silver 1Kg": 0.1,
    "Ham_Petrol_Fiyati 1L": 0.8,
    "Elektrik_Ucreti 1kW": 3,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.02,
    "USD": 1,
    "EUR": 1
}
television_materials = {
    "Aluminum 1Kg": 0.6,
    "Copper 1Kg": 0.5,
    "Gold 1Kg": 0.1,
    "Silver 1Kg": 0.1,
    "Ham_Petrol_Fiyati 1L": 1.5,
    "Elektrik_Ucreti 1kW": 2,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.015,
    "USD": 1,
    "EUR": 1
}
refrigerator_materials = {
    "Aluminum 1Kg": 0.3,
    "Copper 1Kg": 0.2,
    "Gold 1Kg": 0.05,
    "Silver 1Kg": 0.05,
    "Ham_Petrol_Fiyati 1L": 0.9,
    "Elektrik_Ucreti 1kW": 2.5,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 1,
    "EUR": 1
}
printer_materials = {
    "Aluminum 1Kg": 0.2,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 0.4,
    "Elektrik_Ucreti 1kW": 1.5,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 0.9,
    "EUR": 1
}
camera_materials = {
    "Aluminum 1Kg": 0.3,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0.02,
    "Silver 1Kg": 0.05,
    "Ham_Petrol_Fiyati 1L": 0.6,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.02,
    "USD": 1,
    "EUR": 1
}
electricKettle_materials = {
    "Aluminum 1Kg": 0.15,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 0.7,
    "Elektrik_Ucreti 1kW": 0.8,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.01,
    "USD": 0.9,
    "EUR": 1
}
blender_materials = {
    "Aluminum 1Kg": 0.2,
    "Copper 1Kg": 0.1,
    "Gold 1Kg": 0,
    "Silver 1Kg": 0.02,
    "Ham_Petrol_Fiyati 1L": 0.5,
    "Elektrik_Ucreti 1kW": 1,
    "Asgari_Ucret 1 iş günü": 0,
    "Dogal_Gaz 100m^3": 0.015,
    "USD": 0.8,
    "EUR": 1
}

insert_daily_costs("CopperCable 1m", copperCable_materials)
insert_daily_costs("GoldCable 1m", GoldCable_materials)
insert_daily_costs("USBCable", USBCable_materials)
insert_daily_costs("SilverCable 1m", silverCable_materials)
insert_daily_costs("Toy_Car", toy_Car_materials)
insert_daily_costs("Toy_AliminumGun", toy_AliminumGun_materials)
insert_daily_costs("Toy_TeddyBear", toy_TeddyBear_materials)
insert_daily_costs("GamePad", gamePad_materials)
insert_daily_costs("Laptop", laptop_materials)
insert_daily_costs("Smartphone", smartphone_materials)
insert_daily_costs("Tablet", tablet_materials)
insert_daily_costs("Smart Watch", smartwatch_materials)
insert_daily_costs("Gaming Mouse", gamingMouse_materials)
insert_daily_costs("Electric Fan", electricFan_materials)
insert_daily_costs("Microwave", microwave_materials)
insert_daily_costs("Vacuum Cleaner", vacuumCleaner_materials)
insert_daily_costs("Air Conditioner", airConditioner_materials)
insert_daily_costs("Television", television_materials)
insert_daily_costs("Refrigerator", refrigerator_materials)
insert_daily_costs("Printer", printer_materials)
insert_daily_costs("Camera", camera_materials)
insert_daily_costs("Electric Kettle", electricKettle_materials)
insert_daily_costs("Blender", blender_materials)
