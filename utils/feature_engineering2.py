def extract_features_from_shop(shop_docs):
    import numpy as np

    all_prices = []
    product_price_series = {}  # Ürün bazlı fiyat serileri

    for doc in shop_docs:
        for manu in [f"Man{i} Products" for i in range(1, 26)]:
            if manu in doc:
                for key, value in doc[manu].items():
                    if "Price" in key:
                        pname_key = key.replace(" Price", "")
                        pname = doc[manu].get(pname_key)
                        if pname:
                            price = float(value.replace(",", "").replace(" TL", ""))
                            all_prices.append(price)
                            if pname not in product_price_series:
                                product_price_series[pname] = []
                            product_price_series[pname].append((doc["Date"], price))

    # Tüm fiyatlar için genel istatistikler
    avg_price = np.mean(all_prices) if all_prices else 0
    std_price = np.std(all_prices) if all_prices else 0
    min_price = np.min(all_prices) if all_prices else 0
    max_price = np.max(all_prices) if all_prices else 0
    q1_price = np.percentile(all_prices, 25) if all_prices else 0
    q3_price = np.percentile(all_prices, 75) if all_prices else 0
    count_prices = len(all_prices)

    # Ürün bazlı zam analizi
    zam_freqs = []
    zam_std_devs = []
    sync_zam_counts = []

    date_set = set()
    for prices in product_price_series.values():
        prices.sort()
        last_price = None
        last_date = None
        zam_days = []
        zam_ratios = []

        for date, price in prices:
            if last_price is not None:
                if price > last_price * 1.01:  # %1'den fazla artış varsa zam diyelim
                    days_passed = (date - last_date).days
                    zam_days.append(days_passed)
                    zam_ratios.append((price - last_price) / last_price)
                    date_set.add(date)

            last_price = price
            last_date = date

        if zam_days:
            zam_freqs.append(np.mean(zam_days))
        if zam_ratios:
            zam_std_devs.append(np.std(zam_ratios))

    # Zam yapılan günlerde kaç ürün var
    if date_set:
        sync_ratio = len(date_set) / 115  # 115 günümüz var toplam
    else:
        sync_ratio = 0

    feature_vector = [
        avg_price,
        std_price,
        min_price,
        max_price,
        q1_price,
        q3_price,
        count_prices,
        np.mean(zam_freqs) if zam_freqs else 0,
        np.mean(zam_std_devs) if zam_std_devs else 0,
        sync_ratio
    ]
    return feature_vector
