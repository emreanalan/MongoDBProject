import pymongo
from datetime import datetime, timedelta
from pprint import pprint

client = pymongo.MongoClient("mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["DataSet"]

# === Yardımcı === #
def extract_price(val):
    if not val:
        return None
    return float(val.replace(" TL", "").replace(",", ""))

# === Test Fonksiyonu === #
def test_collusion_group(group_shops: list, collusion_products: list, zam_days: list, delays: dict):
    print("\n==============================")
    print(f"🧪 Test başlatıldı: {group_shops}")
    print("==============================")

    leader = group_shops[0]
    success = True

    for zam_day in zam_days:
        print(f"\n🔎 Test edilen zam günü: {zam_day.strftime('%Y-%m-%d')}")
        leader_doc = db[leader].find_one({"Date": zam_day})
        if not leader_doc:
            print(f"❌ Lider {leader} verisi eksik.")
            success = False
            continue

        for manu_key in leader_doc:
            if "Products" not in manu_key:
                continue
            for i in range(1, 21):
                pname = leader_doc[manu_key].get(f"Product {i}")
                if pname not in collusion_products:
                    continue
                leader_price = extract_price(leader_doc[manu_key].get(f"Product {i} Price"))

                for follower in group_shops[1:]:
                    delay_day = zam_day + timedelta(days=delays[follower])
                    f_doc = db[follower].find_one({"Date": delay_day})
                    if not f_doc:
                        print(f"❌ {follower} verisi eksik: {delay_day}")
                        success = False
                        continue
                    f_price = None
                    for f_key in f_doc:
                        if "Products" in f_key and f_doc[f_key].get(f"Product {i}") == pname:
                            f_price = extract_price(f_doc[f_key].get(f"Product {i} Price"))
                            break
                    if f_price is None:
                        print(f"❌ {follower} ürünü bulamadı: {pname}")
                        success = False
                    elif abs(leader_price - f_price) > 0.05:
                        print(f"❌ {follower} fiyat uyumsuz: {pname} {leader_price} ≠ {f_price}")
                        success = False
                    else:
                        print(f"✅ {follower} doğru fiyatladı: {pname} | Lider: {leader_price:.2f} | Takipçi: {f_price:.2f} | Fark: {abs(leader_price - f_price):.2f}")

    if success:
        print("\n🎯 Grup testi BAŞARILI ✅")
    else:
        print("\n⚠️ Grup testi BAŞARISIZ ❌")

# === Örnek Kullanım === #
if __name__ == "__main__":
    test_collusion_group(
        group_shops=["Shop 13", "Shop 5", "Shop 19", "Shop 18"],
        collusion_products=[
            "Product 218", "Product 219", "Product 146", "Product 154", "Product 205",
            "Product 156", "Product 151", "Product 216"
        ],
        zam_days=[
            datetime(2025, 1, 10), datetime(2025, 2, 19),
            datetime(2025, 3, 10), datetime(2025, 3, 25)
        ],
        delays={"Shop 13": 0, "Shop 5": 1, "Shop 19": 5, "Shop 18": 7}
    )
