import os
import json
import matplotlib.pyplot as plt
from datetime import datetime

def load_collusion_group_shops(group_id, collusion_groups_dict):
    return collusion_groups_dict.get(group_id, [])

def parse_price(value):
    try:
        return float(value.replace(",", "").replace(" TL", ""))
    except:
        return None

def extract_product_price_over_time(shop_json_path, product_name):
    with open(shop_json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    price_over_time = []
    for day_record in records:
        date_str = day_record.get("Date")
        if not date_str:
            continue
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

        for manu_key, products in day_record.items():
            if not manu_key.endswith("Products"):
                continue

            # 1. Find the matching Product X for the target product name
            matching_index = None
            for key, value in products.items():
                if key.startswith("Product ") and not key.endswith("Price") and value == product_name:
                    matching_index = key.split()[1]  # e.g., "Product 4" → "4"
                    break

            if matching_index:
                price_key = f"Product {matching_index} Price"
                price_value = products.get(price_key)
                if price_value:
                    price = parse_price(price_value)
                    if price is not None:
                        price_over_time.append((date_obj, price))
    return sorted(price_over_time)


def plot_price_graph(group_id, product_name, shop_folder, collusion_groups):
    shop_ids = load_collusion_group_shops(group_id, collusion_groups)
    if not shop_ids:
        print(f"Group {group_id} not found.")
        return

    plt.figure(figsize=(12, 6))
    for shop_id in shop_ids:
        shop_path = os.path.join(shop_folder, f"Shop {shop_id}.json")
        if not os.path.exists(shop_path):
            print(f"Shop file not found: {shop_path}")
            continue

        price_data = extract_product_price_over_time(shop_path, product_name)
        if not price_data:
            continue

        dates, prices = zip(*price_data)
        plt.plot(dates, prices, label=f"Shop {shop_id}")

    plt.title(f"Price Trend for '{product_name}' in Collusion Group {group_id}")
    plt.xlabel("Date")
    plt.ylabel("Price (TRY)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    COLLUSION_GROUPS = {
        1: [231, 240, 201, 330, 7, 88, 94, 136, 286, 35],
        2: [15, 303, 334, 72, 81, 87, 200, 180, 366, 253],
        3: [117, 192, 181, 390, 272, 378, 317, 90, 214, 49],
        4: [148, 389, 20, 376, 295, 63, 374, 199, 61, 134],
        5: [237, 270, 48, 105, 212, 224, 89, 174, 349, 34],
        6: [215, 47, 77, 64, 320, 31, 163, 309, 266, 182],
        7: [65, 347, 187, 368, 186, 249, 66, 271, 82, 398],
        8: [323, 16, 104, 197, 170, 189, 379, 338, 331, 99],
        9: [377, 245, 55, 344, 84, 372, 58, 350, 242, 30],
        10: [322, 391, 83, 145, 358, 60, 382, 71, 11, 159],
        11: [387, 184, 283, 111, 167, 43, 40, 236, 274, 234],
        12: [363, 115, 107, 258, 227, 32, 232, 298, 42, 357],
        13: [86, 95, 108, 332, 205, 156, 176, 304, 318, 218],
        14: [259, 70, 12, 273, 251, 230, 337, 209, 1, 252],
        15: [109, 37, 305, 79, 342, 68, 144, 278, 354, 307],
        16: [76, 203, 254, 110, 92, 39, 207, 261, 292, 194],
        17: [113, 153, 371, 210, 73, 188, 395, 33, 364, 360],
        18: [228, 345, 359, 291, 139, 21, 127, 220, 13, 399],
        19: [4, 18, 53, 114, 313, 392, 152, 178, 280, 325],
        20: [129, 238, 80, 164, 133, 179, 315, 46, 311, 297],
    }
    shop_folder_path = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/exported_shops3"  # Update this path to your shop folder
    product_to_plot = "Product 244"
    group_to_plot = 1

    plot_price_graph(group_to_plot, product_to_plot, shop_folder_path, COLLUSION_GROUPS)
