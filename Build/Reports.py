import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np

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
