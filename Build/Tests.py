import pymongo
from collections import defaultdict
from datetime import timedelta
import numpy as np

# === MongoDB Bağlantısı ===
client = pymongo.MongoClient(
    "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["DataSet"]

# === Gerçek Gecikme Bilgileri ===
real_delays = {
    "ShopGroup_1": {
        "Shop 392": 4,
        "Shop 390": 7,
        "Shop 372": 3,
    },
    "ShopGroup_2": {
        "Shop 375": 3,
        "Shop 386": 5,
        "Shop 399": 3,
    },
    "ShopGroup_3": {
        "Shop 380": 4,
        "Shop 396": 3,
        "Shop 382": 1,
        "Shop 376": 1,
    },
    "ShopGroup_4": {
        "Shop 394": 7,
        "Shop 389": 6,
        "Shop 395": 6,
        "Shop 379": 5,
    },
    "ShopGroup_5": {
        "Shop 400": 2,
        "Shop 398": 5,
        "Shop 371": 4,
        "Shop 381": 1,
    },
    "ShopGroup_6": {
        "Shop 397": 1,
        "Shop 385": 5,
        "Shop 384": 2,
    },
    "ShopGroup_7": {
        "Shop 373": 6,
        "Shop 383": 5,
    }
}





# === Yardımcı Fonksiyonlar ===

def extract_product_series(docs):
    """Tüm ürünler için zaman serisi çıkarır"""
    series = defaultdict(list)

    for doc in docs:
        date = doc["Date"]
        for key, content in doc.items():
            if "Products" in key:
                for i in range(1, 21):
                    pname = content.get(f"Product {i}")
                    pprice = content.get(f"Product {i} Price")
                    if pname and pprice:
                        price = float(pprice.replace(",", "").replace(" TL", ""))
                        series[pname].append((date, price))
    return series

def test_follower_exact(leader_series, follower_series, delay_days):
    """Follower tam gecikme ile lideri doğru takip ediyor mu kontrol eder"""
    results = {}

    for pname, l_data in leader_series.items():
        f_data = follower_series.get(pname)
        if not f_data:
            results[pname] = False
            continue

        # Tarih kaydırması uygula
        shifted_follower = [(date - timedelta(days=delay_days), price) for date, price in f_data]

        # Dictionary yap
        l_dict = {date: price for date, price in l_data}
        f_dict = {date: price for date, price in shifted_follower}

        # Ortak tarihlerde karşılaştır
        common_dates = set(l_dict.keys()) & set(f_dict.keys())
        if not common_dates:
            results[pname] = False
            continue

        is_correct = all(abs(l_dict[d] - f_dict[d]) < 1e-2 for d in common_dates)
        results[pname] = is_correct

    return results

# === Ana Test Fonksiyonu ===

def run_full_collusion_test():
    print("🚀 CollusionShops Kapsamlı Uyum Testi Başlatıldı!\n")

    total_correct = 0
    total_tests = 0

    for group_name, followers in real_delays.items():
        print(f"🔵 {group_name} test ediliyor...\n")

        collection = db[group_name]
        docs = list(collection.find({}, {"_id": 0}))

        # Tüm Shopları ayır
        shop_docs = defaultdict(list)
        for doc in docs:
            shop_docs[doc["Shop Name"]].append(doc)

        # Lider Shop'u bul
        possible_leaders = [shop for shop in shop_docs if shop not in followers]
        if not possible_leaders:
            print(f"⚠️ {group_name} için lider bulunamadı!")
            continue

        leader_shop = possible_leaders[0]
        leader_series = extract_product_series(shop_docs[leader_shop])

        for follower_shop, delay in followers.items():
            follower_series = extract_product_series(shop_docs[follower_shop])

            results = test_follower_exact(leader_series, follower_series, delay)
            correct = sum(v for v in results.values())
            total = len(results)

            total_correct += correct
            total_tests += total

            uyum = (correct / total) * 100 if total > 0 else 0
            print(f"🛒 {follower_shop}: {correct}/{total} ürün doğru takip | Uyum: %{uyum:.2f}")

            # Hatalı ürünleri listele
            for pname, is_correct in results.items():
                if not is_correct:
                    print(f"   ❌ Hatalı Ürün: {pname}")

    print("\n=====================")
    overall = (total_correct / total_tests) * 100 if total_tests > 0 else 0
    print(f"🌟 Toplam Uyum: %{overall:.2f} ({total_correct}/{total_tests} doğru)")
    print("=====================\n")

# === Main Çalıştırıcı ===
if __name__ == "__main__":
    run_full_collusion_test()
