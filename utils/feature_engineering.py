def extract_features_for_shop(shop_name, db):
    cursor = db[shop_name].find({})
    days_with_price_increase = 0
    total_price_increase_pct = 0
    total_products_updated = 0
    total_profit_pct = 0
    total_entries = 0
    collusion_products = []  # Yeni: Collusion ürünleri

    for doc in cursor:
        for key in doc:
            if "Products" in key:
                manu_doc = doc[key]
                for i in range(1, 21):
                    pname = manu_doc.get(f"Product {i}")
                    price_str = manu_doc.get(f"Product {i} Price")
                    base_str = manu_doc.get(f"Product {i} Manufacturer Price")
                    profit = manu_doc.get(f"Product {i} Shop Profit %")

                    if pname and price_str and base_str:
                        try:
                            price = float(price_str.replace(" TL", "").replace(",", ""))
                            base = float(base_str.replace(" TL", "").replace(",", ""))
                            pct_increase = (price - base) / base
                            total_price_increase_pct += pct_increase
                            total_products_updated += 1
                            if pct_increase > 0.01:
                                days_with_price_increase += 1
                            if profit:
                                total_profit_pct += float(profit)
                            total_entries += 1

                            # Yeni: Eğer collusion ürünü ise, listeye ekleyelim
                            if pname in collusion_products:
                                collusion_products.append(pname)
                        except:
                            continue

    avg_price_increase_pct = total_price_increase_pct / total_products_updated if total_products_updated else 0
    price_increase_frequency = 115 / days_with_price_increase if days_with_price_increase else 115
    avg_products_updated_per_zam = total_products_updated / days_with_price_increase if days_with_price_increase else 0
    avg_profit_pct = total_profit_pct / total_entries if total_entries else 0

    return {
        "shop": shop_name,
        "avg_price_increase_pct": round(avg_price_increase_pct, 4),
        "num_price_increase_days": days_with_price_increase,
        "price_increase_frequency": round(price_increase_frequency, 2),
        "avg_products_updated_per_zam": round(avg_products_updated_per_zam, 2),
        "avg_profit_pct": round(avg_profit_pct, 2),
        "num_collusion_products": len(collusion_products)  # Yeni: Collusion ürün sayısı
    }
