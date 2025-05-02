import os
import json
import pandas as pd
from glob import glob
from statistics import mean, stdev
from datetime import datetime


# --- Yardımcı Fonksiyonlar ---
def parse_price(val):
    try:
        return float(val.replace(" TL", "").replace(".", "").replace(",", "."))
    except:
        return None


def extract_zam_days(records):
    zam_days = set()
    prev_prices = {}
    for record in records:
        date = datetime.strptime(record["Date"], "%Y-%m-%d")
        for key in record:
            if "Products" in key:
                products = record[key]
                for prod_key in products:
                    if "Price" in prod_key:
                        pname = prod_key.split("Price")[0].strip()
                        price = parse_price(products[prod_key])
                        if pname in prev_prices and price is not None:
                            if abs(prev_prices[pname] - price) > 1:
                                zam_days.add(date)
                        prev_prices[pname] = price
    return sorted(zam_days)


# --- Ana İşlem ---
def feature_engineering(input_folder, output_csv=None):
    shop_files = sorted(glob(os.path.join(input_folder, "Shop *.json")))
    detailed_features = []

    for file_path in shop_files:
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        shop_name = os.path.basename(file_path).replace(".json", "")
        profit_list = []
        zam_oran_list = []
        manufacturer_set = set()
        price_prev = {}

        zam_gunleri = extract_zam_days(records)
        total_days = len(records)
        zam_day_count = len(zam_gunleri)
        zam_frequency = round(zam_day_count / total_days * 100, 2) if total_days > 0 else 0

        for day in records:
            for key in day:
                if "Products" in key:
                    manufacturer_set.add(key)
                    products = day[key]
                    for pk in products:
                        if "Shop Profit %" in pk:
                            profit_list.append(products[pk])
                        if "Price" in pk:
                            pname = pk.split("Price")[0].strip()
                            price = parse_price(products[pk])
                            if pname in price_prev and price is not None:
                                delta = price - price_prev[pname]
                                if abs(delta) > 1:
                                    rate = (delta / price_prev[pname]) * 100 if price_prev[pname] else 0
                                    zam_oran_list.append(rate)
                            price_prev[pname] = price

        # Özellik hesaplama
        avg_profit = round(mean(profit_list), 2) if profit_list else 0
        std_profit = round(stdev(profit_list), 2) if len(profit_list) > 1 else 0
        avg_zam_orani = round(mean(zam_oran_list), 2) if zam_oran_list else 0
        std_zam_orani = round(stdev(zam_oran_list), 2) if len(zam_oran_list) > 1 else 0

        detailed_features.append({
            "Shop": shop_name,
            "Avg Profit %": avg_profit,
            "Std Profit %": std_profit,
            "Zam Gün Sayısı": zam_day_count,
            "Zam Günlük Yoğunluk (%)": zam_frequency,
            "Avg Zam Oranı %": avg_zam_orani,
            "Std Zam Oranı %": std_zam_orani,
            "Manufacturer Sayısı": len(manufacturer_set)
        })

    df = pd.DataFrame(detailed_features)

    if output_csv:
        df.to_csv(output_csv, index=False)
        print(f"✅ Özellik tablosu kaydedildi: {output_csv}")
        print(df.head())  # Kontrol amaçlı, ilk 5 satırı basar
    else:
        print(df.head())

    return df


def load_zam_and_manufacturer_data(shop_dir):
    zam_gunleri = {}
    manufacturers = {}

    shop_files = sorted(glob(os.path.join(shop_dir, "Shop *.json")))

    for file_path in shop_files:
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        shop_name = os.path.basename(file_path).replace(".json", "")
        gunler = set()
        mans = set()

        for record in records:
            try:
                date = datetime.strptime(record["Date"], "%Y-%m-%d").date()
                for key in record:
                    if "Products" in key:
                        mans.add(key.replace(" Products", ""))
                        gunler.add(date)
                        break
            except:
                continue

        zam_gunleri[shop_name] = gunler
        manufacturers[shop_name] = mans

    return zam_gunleri, manufacturers



# --- Kullanım Örneği ---
if __name__ == "__main__":
    feature_engineering("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops", "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/utils/shop_features.csv")

