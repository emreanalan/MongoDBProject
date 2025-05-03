import pandas as pd

def label_shops(input_csv, collusion_shop_names, output_csv="C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/utils/shop_features_labeled.csv"):
    # CSV dosyasını oku
    df = pd.read_csv(input_csv)

    # Etiket ekle: 1 = Collusion, 0 = Normal
    df["Label"] = df["Shop"].apply(lambda x: 1 if x in collusion_shop_names else 0)

    # Yeni CSV'ye yaz
    df.to_csv(output_csv, index=False)
    print(f"✅ Etiketli veri kaydedildi: {output_csv}")

    return df

# --- Kullanım Örneği ---
if __name__ == "__main__":
    collusion_shops = [
        "Shop 2", "Shop 10", "Shop 11", "Shop 12", "Shop 15", "Shop 18", "Shop 19",
        "Shop 21", "Shop 23", "Shop 26", "Shop 29", "Shop 30", "Shop 33", "Shop 34",
        "Shop 35", "Shop 40", "Shop 41", "Shop 42", "Shop 44", "Shop 45", "Shop 46",
        "Shop 47", "Shop 48", "Shop 49", "Shop 50", "Shop 52", "Shop 53", "Shop 54",
        "Shop 55", "Shop 59", "Shop 60", "Shop 62", "Shop 63", "Shop 65", "Shop 67",
        "Shop 68", "Shop 70", "Shop 74", "Shop 75", "Shop 76", "Shop 78", "Shop 80",
        "Shop 84", "Shop 85", "Shop 86", "Shop 88", "Shop 90", "Shop 96", "Shop 98",
        "Shop 99"
    ]

    label_shops("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/utils/shop_features3.csv", collusion_shops)
