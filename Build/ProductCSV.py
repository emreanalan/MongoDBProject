import pandas as pd

# Gerçek gruplar (COLLUSION_GROUPS)
COLLUSION_GROUPS = {
    1: [206, 24, 33],
    2: [164, 57, 174],
    3: [246, 317, 349],
    4: [169, 138, 343],
    5: [218, 60, 153, 399],
    6: [78, 160, 320],
    7: [347, 139, 199],
    8: [225, 83, 167],
    9: [273, 373, 187, 31],
    10: [110, 369, 217, 259, 323],
    11: [275, 350, 230, 130, 38],
    12: [330, 111, 345, 190, 18],
    13: [336, 147, 173, 387],
    14: [265, 254, 232, 372, 148],
    15: [172, 315, 316, 34],
    16: [84, 353, 103, 381, 329],
    17: [354, 17, 376],
    18: [65, 135, 270, 331, 359],
    19: [140, 289, 6, 3],
    20: [374, 93, 357],
    21: [76, 157, 342],
    22: [131, 386, 101],
    23: [327, 221, 303],
    24: [249, 122, 26, 299],
    25: [318, 278, 192, 352],
    26: [116, 227, 128, 9, 371],
    27: [88, 311, 42, 19, 292],
    28: [314, 392, 46, 114],
    29: [189, 222, 145, 87],
    30: [29, 396, 358],
    31: [13, 228, 161],
    32: [240, 180, 129, 21],
    33: [94, 163, 271, 364, 12],
    34: [16, 177, 150, 142],
    35: [32, 324, 121],
    36: [165, 291, 389, 155],
    37: [80, 143, 119, 201],
    38: [113, 197, 186],
    39: [212, 209, 319],
    40: [356, 178, 8, 184],
    41: [379, 281, 55, 64, 30],
    42: [66, 51, 332],
    43: [298, 58, 214, 306],
    44: [132, 90, 40],
    45: [202, 220, 127, 264, 257],
    46: [95, 43, 384, 368, 195],
    47: [391, 321, 313],
    48: [378, 205, 22],
    49: [312, 250, 223, 1],
    50: [28, 276, 52, 280, 100],
    51: [162, 56, 54],
    52: [47, 75, 120, 211, 334],
    53: [144, 27, 67, 253, 393],
    54: [118, 248, 194, 252],
    55: [96, 279, 307],
    56: [207, 367, 296, 301],
    57: [337, 305, 288, 198, 302],
    58: [297, 261, 191, 251, 274],
    59: [71, 383, 310, 35],
    60: [20, 152, 185],
    61: [326, 154, 85, 134],
    62: [151, 204, 25, 82],
    63: [215, 89, 73, 322, 355],
    64: [269, 98, 105, 304, 69],
    65: [333, 4, 287, 92, 79],
    66: [263, 2, 294],
    67: [233, 285, 235],
    68: [335, 390, 68, 141, 266],
    69: [196, 338, 341, 203],
    70: [377, 308, 286, 224],
    71: [14, 394, 125],
    72: [200, 351, 243, 115, 11],
    73: [170, 37, 219, 216, 210],
    74: [23, 39, 244, 234, 171],
    75: [268, 339, 63],
    76: [74, 267, 365, 229],
}

# Adım 1: Gerçek grup eşlemesi oluştur
true_group_map = {shop: group for group, shops in COLLUSION_GROUPS.items() for shop in shops}

# Adım 2: Veriyi yükle
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1_clustered.csv")
df["shop_id"] = df["shop_id"].astype(int)
df["true_group"] = df["shop_id"].map(true_group_map)

# Adım 3: Her predicted_group için en çok eşleşen true_group'u bul ve doğruluğu hesapla
group_results = {}
for pred_group in df["predicted_group"].unique():
    group_df = df[df["predicted_group"] == pred_group]
    top_true = group_df["true_group"].value_counts()
    if not top_true.empty:
        top_group = top_true.index[0]
        correct = top_true.iloc[0]
        total = group_df["true_group"].notna().sum()
        group_results[pred_group] = {
            "matched_true_group": top_group,
            "group_accuracy": round(correct / total, 3) if total > 0 else 0,
            "group_size": len(group_df),
            "labeled_count": total
        }

# Adım 4: Genel doğruluğu hesapla
total_correct = sum(r["group_accuracy"] * r["labeled_count"] for r in group_results.values())
total_labeled = sum(r["labeled_count"] for r in group_results.values())
overall_accuracy = round(total_correct / total_labeled, 4)

# Sonuçları yazdır
print(f"🔍 Toplam Eşleşen Shop Sayısı: {total_labeled}")
print(f"🎯 Toplam Doğruluk: {overall_accuracy * 100:.2f}%")
