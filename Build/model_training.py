import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# Şu yolu senin verdiğin konuma göre güncelledik
DATA_PATH = "/csv_yedek/shop_features.csv"
df = pd.read_csv(DATA_PATH)

# 1. AŞAMA: Collusion var mı yok mu (Binary Classification)
features = [
    "price_change_count", "avg_day_between_changes", "manufacturer_count",
    "avg_profit_pct", "profit_pct_std", "product_count",
    "avg_delay_score", "exact_overlap_ratio", "avg_profit_similarity"
]

X = df[features]
y_binary = df["label_binary"]

X_train_bin, X_test_bin, y_train_bin, y_test_bin = train_test_split(X, y_binary, test_size=0.25, random_state=42)

clf_bin = RandomForestClassifier(n_estimators=100, random_state=42)
clf_bin.fit(X_train_bin, y_train_bin)

# Binary tahmin
y_pred_bin = clf_bin.predict(X_test_bin)
print("--- Classification Report (Binary) ---")
print(classification_report(y_test_bin, y_pred_bin))

cm_bin = confusion_matrix(y_test_bin, y_pred_bin)
sns.heatmap(cm_bin, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix - Binary Collusion Detection")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# 2. AŞAMA: Collusion olanların grup sınıflandırması
collusion_df = df[df["label_binary"] == 1]
X_group = collusion_df[features]
y_group = collusion_df["label_group"]

X_train_grp, X_test_grp, y_train_grp, y_test_grp = train_test_split(X_group, y_group, test_size=0.25, random_state=42)

clf_grp = RandomForestClassifier(n_estimators=100, random_state=42)
clf_grp.fit(X_train_grp, y_train_grp)

# Grup tahmin
y_pred_grp = clf_grp.predict(X_test_grp)
print("--- Classification Report (Group) ---")
print(classification_report(y_test_grp, y_pred_grp))

cm_grp = confusion_matrix(y_test_grp, y_pred_grp, labels=sorted(y_group.unique()))
sns.heatmap(cm_grp, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix - Collusion Group Classification")
plt.xlabel("Predicted label")
plt.ylabel("True label")
plt.xticks(ticks=np.arange(len(y_group.unique())), labels=sorted(y_group.unique()))
plt.yticks(ticks=np.arange(len(y_group.unique())), labels=sorted(y_group.unique()))
plt.show()

# Model kayıt
# joblib.dump(clf_bin, "model_binary.pkl")
# joblib.dump(clf_grp, "model_group.pkl")