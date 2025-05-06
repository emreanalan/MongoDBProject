import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np

COLLUSION_GROUPS = {
    1: [40, 235, 339, 245, 197, 323, 302, 182, 166, 238],
    2: [319, 16, 67, 172, 332, 21, 255, 12, 265, 75],
    3: [279, 119, 384, 220, 26, 375, 327, 33, 224, 196],
    4: [108, 377, 136, 276, 263, 55, 129, 396, 109, 78],
    5: [118, 234, 395, 30, 7, 159, 41, 160, 207, 130],
    6: [343, 314, 259, 151, 25, 320, 380, 258, 346, 393],
    7: [103, 290, 366, 199, 344, 231, 365, 241, 195, 87],
    8: [248, 308, 225, 183, 269, 387, 74, 371, 353, 192],
    9: [372, 388, 165, 60, 244, 394, 331, 79, 179, 187],
    10: [233, 115, 174, 53, 189, 280, 253, 6, 246, 277],
    11: [66, 201, 383, 101, 200, 205, 120, 285, 44, 378],
    12: [32, 4, 9, 185, 163, 333, 106, 83, 296, 321],
    13: [2, 262, 81, 325, 272, 59, 214, 256, 232, 305],
    14: [247, 138, 23, 306, 202, 313, 99, 328, 283, 278],
    15: [293, 178, 126, 147, 47, 359, 5, 361, 177, 31],
    16: [289, 307, 209, 301, 110, 148, 132, 173, 80, 8],
    17: [391, 287, 284, 3, 369, 88, 385, 273, 291, 354],
    18: [149, 299, 111, 254, 322, 355, 69, 57, 275, 104],
    19: [204, 348, 77, 266, 181, 121, 249, 114, 243, 128],
    20: [29, 351, 146, 36, 125, 329, 218, 105, 316, 72],
    21: [336, 342, 10, 145, 123, 186, 37, 137, 117, 229],
    22: [337, 222, 267, 52, 386, 228, 176, 91, 134, 141],
    23: [156, 382, 180, 50, 297, 155, 360, 191, 18, 398],
    24: [286, 381, 42, 70, 1, 193, 363, 237, 17, 221],
    25: [211, 158, 347, 373, 309, 157, 324, 379, 376, 340],
    26: [274, 28, 150, 251, 124, 374, 226, 294, 90, 356],
    27: [122, 213, 89, 250, 358, 239, 219, 64, 349, 127],
    28: [46, 171, 14, 230, 133, 217, 390, 188, 295, 303],
    29: [317, 335, 236, 19, 24, 107, 330, 35, 45, 210],
    30: [364, 288, 184, 131, 56, 270, 71, 39, 300, 84],
}

# Veriyi oku
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv")

# Tahminler ve gerçek değerler
# Bu kısımlar model çıktısı ile değiştirilmelidir
y_true_binary = df["is_collusion"]
y_pred_binary = df["is_collusion"]  # Örneğin: model.predict(X)

# Sadece collusion shoplar için
df_collusion = df[df["is_collusion"] == 1]
y_true_groups = df_collusion["collusion_group"]
y_pred_groups = df_collusion["collusion_group"]  # Örneğin: clustering sonucu/model çıktısı

def plot_confusion_matrix(cm, classes, title, normalize=False):
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt=".0f" if not normalize else ".2f", cmap="Blues",
                xticklabels=classes, yticklabels=classes)
    plt.title(title)
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()
    plt.show()

def evaluate_binary_collusion(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred)
    print("\nBinary Classification Report (is_collusion):")
    print(classification_report(y_true, y_pred, digits=4))
    plot_confusion_matrix(cm, classes=["Normal", "Collusion"],
                          title="Confusion Matrix - Binary Collusion Detection")

def evaluate_group_classification(y_true, y_pred):
    labels = sorted(list(set(y_true) | set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print("\nMulti-class Classification Report (collusion groups):")
    print(classification_report(y_true, y_pred, labels=labels, digits=4))
    plot_confusion_matrix(cm, classes=labels,
                          title="Confusion Matrix - Collusion Group Classification")

# --- Ana değerlendirme ---
evaluate_binary_collusion(y_true_binary, y_pred_binary)
evaluate_group_classification(y_true_groups, y_pred_groups)
