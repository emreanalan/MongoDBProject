import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.preprocessing import StandardScaler

# Veri yolu
DATA_PATH = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv"
df = pd.read_csv(DATA_PATH)

# Özellik listesi
features = [
    "price_change_count", "avg_day_between_changes", "manufacturer_count",
    "avg_profit_pct", "profit_pct_std", "product_count",
    "avg_delay_score", "exact_overlap_ratio", "avg_profit_similarity"
]

# === AŞAMA 1: BINARY CLASSIFICATION ===
X = df[features]
y_binary = df["label_binary"]

X_train_bin, X_test_bin, y_train_bin, y_test_bin = train_test_split(
    X, y_binary, test_size=0.25, random_state=42, stratify=y_binary
)

clf_bin = RandomForestClassifier(n_estimators=100, random_state=42)
clf_bin.fit(X_train_bin, y_train_bin)

# Binary tahmin
y_pred_bin = clf_bin.predict(X_test_bin)
print("--- Classification Report (Binary) ---")
print(classification_report(y_test_bin, y_pred_bin))

cm_bin = confusion_matrix(y_test_bin, y_pred_bin)
plt.figure(figsize=(5, 4))
sns.heatmap(cm_bin, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix - Binary Collusion Detection")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.show()

# Özellik önem dereceleri
print("\n📌 Feature Importances (Binary Classification):")
importances_bin = clf_bin.feature_importances_
for feat, imp in sorted(zip(features, importances_bin), key=lambda x: -x[1]):
    print(f"{feat}: {imp:.4f}")

# === AŞAMA 2: SUPERVISED GROUP CLASSIFICATION ===
df["pred_binary"] = clf_bin.predict(X)
predicted_collusion_df = df[df["pred_binary"] == 1].copy()

X_group = predicted_collusion_df[features]
y_group = predicted_collusion_df["label_group"]

X_train_grp, X_test_grp, y_train_grp, y_test_grp = train_test_split(
    X_group, y_group, test_size=0.30, random_state=42, stratify=y_group
)

clf_grp = RandomForestClassifier(n_estimators=100, random_state=42)
clf_grp.fit(X_train_grp, y_train_grp)

y_pred_grp = clf_grp.predict(X_test_grp)
print("--- Classification Report (Group - Supervised) ---")
print(classification_report(y_test_grp, y_pred_grp, zero_division=0))

cm_grp = confusion_matrix(y_test_grp, y_pred_grp, labels=sorted(y_group.unique()))
plt.figure(figsize=(24, 14))
sns.heatmap(cm_grp, annot=True, fmt=".0f", cmap="Blues")
plt.title("Confusion Matrix - Collusion Group Classification (Supervised)")
plt.xlabel("Predicted label")
plt.ylabel("True label")
plt.xticks(ticks=np.arange(len(cm_grp[0])) + 0.5, labels=sorted(y_group.unique()), rotation=90)
plt.yticks(ticks=np.arange(len(cm_grp)) + 0.5, labels=sorted(y_group.unique()), rotation=0)
plt.tight_layout()
plt.show()

# Model kayıt
# joblib.dump(clf_bin, "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Models/model_binary.pkl")
# joblib.dump(clf_grp, "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Models/model_group_supervised.pkl")