import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.signal import correlate
from datetime import timedelta

from DataRetrieval import fetch_price_data, calculate_daily_percentage_change

def compute_product_based_cosine_similarity(df: pd.DataFrame, similarity_threshold=0.75, max_delay_days=7):
    """
    Computes leader-follower relationships between shops for each product based on daily price changes.

    Args:
    - df (pd.DataFrame): DataFrame with ['shop_id', 'product_name', 'date', 'daily_change']
    - similarity_threshold (float): minimum cosine similarity to accept as similar (default 0.75)
    - max_delay_days (int): maximum delay (in days) tolerated between leader and follower (default 7)

    Returns:
    - List[Dict]: [{'product_name': X, 'leader_shop': Y, 'follower_shop': Z, 'similarity': S, 'delay_days': D}, ...]
    """
    results = []

    # Step 1: Get unique products
    products = df['product_name'].unique()

    for product in products:
        # Step 2: Filter data for this product
        product_df = df[df['product_name'] == product]

        # Pivot to create a matrix: rows = date, columns = shop_id, values = daily_change
        pivot_table = product_df.pivot_table(index='date', columns='shop_id', values='daily_change')

        # Drop shops that have too many NaNs
        pivot_table = pivot_table.dropna(axis=1, thresh=int(0.7 * len(pivot_table)))  # Keep only shops with at least 70% data

        if pivot_table.shape[1] < 2:
            continue  # Skip if less than 2 shops left

        # Fill missing values with 0 (no change = 0)
        pivot_table = pivot_table.fillna(0)

        # Step 3: Compute cosine similarity
        cosine_sim = cosine_similarity(pivot_table.T)  # Transpose because we want shop-to-shop
        shop_ids = pivot_table.columns.tolist()

        # Step 4: Find leader-follower pairs
        for i in range(len(shop_ids)):
            for j in range(len(shop_ids)):
                if i == j:
                    continue  # Skip same shop

                similarity = cosine_sim[i, j]

                if similarity >= similarity_threshold:
                    # Step 5: Compute delay between shops using cross-correlation
                    series_i = pivot_table.iloc[:, i].values
                    series_j = pivot_table.iloc[:, j].values

                    corr = correlate(series_j, series_i, mode='full')  # Cross-correlation
                    lag_array = np.arange(-len(series_i) + 1, len(series_j))
                    delay_in_days = lag_array[np.argmax(corr)]

                    if abs(delay_in_days) <= max_delay_days:
                        # Record the leader-follower relationship
                        results.append({
                            'product_name': product,
                            'leader_shop': shop_ids[i],
                            'follower_shop': shop_ids[j],
                            'similarity': round(float(similarity), 4),
                            'delay_days': int(delay_in_days)
                        })

    return results


def compute_shop_based_cosine_similarity(df: pd.DataFrame, target_shops: list, similarity_threshold=0.75, max_delay_days=7):
    """
    Computes cosine similarity and delay between given shops based on all product daily changes combined.

    Args:
    - df (pd.DataFrame): Must contain ['shop_id', 'product_name', 'date', 'daily_change']
    - target_shops (list): List of shop_ids to compare (e.g., ["YourElectrician", "MyElectrician", "HisElectrician"])
    - similarity_threshold (float): Cosine similarity threshold (default 0.75)
    - max_delay_days (int): Maximum delay in days tolerated (default 7)

    Returns:
    - List[Dict]: [{'leader_shop': Y, 'follower_shop': Z, 'similarity': S, 'delay_days': D}]
    """
    results = []

    # Filter only target shops
    target_df = df[df['shop_id'].isin(target_shops)]

    # Pivot: rows = date, columns = shop_id, values = average daily change across all products
    pivot_table = target_df.groupby(['date', 'shop_id'])['daily_change'].mean().unstack()

    # Drop shops with too many missing values
    pivot_table = pivot_table.dropna(axis=1, thresh=int(0.7 * len(pivot_table)))  # Keep shops with at least 70% data

    if pivot_table.shape[1] < 2:
        print("Not enough shops after cleaning.")
        return []

    # Fill missing values with 0
    pivot_table = pivot_table.fillna(0)

    # Compute cosine similarity
    cosine_sim = cosine_similarity(pivot_table.T)
    shop_ids = pivot_table.columns.tolist()

    for i in range(len(shop_ids)):
        for j in range(len(shop_ids)):
            if i == j:
                continue

            similarity = cosine_sim[i, j]

            if similarity >= similarity_threshold:
                # Cross-correlation for delay
                series_i = pivot_table.iloc[:, i].values
                series_j = pivot_table.iloc[:, j].values

                corr = correlate(series_j, series_i, mode='full')
                lag_array = np.arange(-len(series_i) + 1, len(series_j))
                delay_in_days = lag_array[np.argmax(corr)]

                if abs(delay_in_days) <= max_delay_days:
                    results.append({
                        'leader_shop': shop_ids[i],
                        'follower_shop': shop_ids[j],
                        'similarity': round(float(similarity), 4),
                        'delay_days': int(delay_in_days)
                    })

    return results


def compute_product_price_similarity(df: pd.DataFrame, target_shops: list, similarity_threshold=0.75):
    """
    Computes cosine similarity between shops based on product price levels (more tolerant).

    Args:
    - df: ['shop_id', 'product_name', 'date', 'price']
    - target_shops: Shops to compare
    - similarity_threshold: Similarity threshold

    Returns:
    - List[Dict]: [{'leader_shop': Y, 'follower_shop': Z, 'similarity': S}]
    """
    results = []

    target_df = df[df['shop_id'].isin(target_shops)]

    # Pivot: rows = product_name, columns = shop_id, values = latest price
    latest_prices = target_df.sort_values('date').groupby(['product_name', 'shop_id']).last().reset_index()
    pivot_table = latest_prices.pivot_table(index='product_name', columns='shop_id', values='price')

    # --- Toleransı arttırıyoruz (%30 yeter)
    # pivot_table = pivot_table.dropna(axis=1, thresh=int(0.1 * len(pivot_table)))

    if pivot_table.shape[1] < 2:
        print("Not enough shops after cleaning (product-level check).")
        return []

    # --- Eksik ürünleri ortalama fiyatla dolduruyoruz
    pivot_table = pivot_table.fillna(pivot_table.mean())

    # --- Normalization: price seviyesini eşitliyoruz
    pivot_table = (pivot_table - pivot_table.mean()) / pivot_table.std()

    # --- Cosine Similarity hesaplama
    cosine_sim = cosine_similarity(pivot_table.T)
    shop_ids = pivot_table.columns.tolist()

    for i in range(len(shop_ids)):
        for j in range(len(shop_ids)):
            if i == j:
                continue

            similarity = cosine_sim[i, j]

            if similarity >= similarity_threshold:
                results.append({
                    'leader_shop': shop_ids[i],
                    'follower_shop': shop_ids[j],
                    'similarity': round(float(similarity), 4)
                })

    return results





# 1. Fetch and process data
df_prices = fetch_price_data("2025-01-23", "2025-04-17")
df_with_changes = calculate_daily_percentage_change(df_prices)

# Define shops
target_shops = ["YourElectrician", "MyElectrician", "HisElectrician"]

# # 2. Find collusion
# collusion_results = compute_product_based_cosine_similarity(df_with_changes)
#
# # 3. Print results
# for result in collusion_results:
#     print(result)
#
#
# # Define shops
# target_shops = ["YourElectrician", "MyElectrician", "HisElectrician"]
#
# # Detect collusion
# shop_collusion_results = compute_shop_based_cosine_similarity(df_with_changes, target_shops)
#
# # Print results
# for result in shop_collusion_results:
#     print(result)

# Detect collusion based on product prices
shop_price_collusion_results = compute_product_price_similarity(df_prices, target_shops)
for result in shop_price_collusion_results:
    print(result)
