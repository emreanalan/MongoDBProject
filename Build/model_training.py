import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Veriyi oku
df = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features1.csv")

# Özellik ve etiketleri ayır
X = df.drop(columns=["shop_id", "is_collusion", "collusion_group"])
y_binary = df["is_collusion"]

# ---------- 1. AŞAMA: Binary Collusion Detection ----------
# Veriyi ayır
X_train, X_test, y_train, y_test = train_test_split(X, y_binary, test_size=0.2, random_state=42)

# Modeli eğit
clf_binary = RandomForestClassifier(random_state=42)
clf_binary.fit(X_train, y_train)

# Tahmin yap
y_pred_binary = clf_binary.predict(X_test)

# Değerlendir
def plot_confusion_matrix(cm, labels, title):
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.tight_layout()
    plt.show()

print("\n[1] Binary Collusion Detection")
print(classification_report(y_test, y_pred_binary, digits=4))
cm_binary = confusion_matrix(y_test, y_pred_binary)
plot_confusion_matrix(cm_binary, ["Normal", "Collusion"], "Confusion Matrix - Binary Classification")

# ---------- 2. AŞAMA: Collusion Group Classification ----------
# Sadece test setinde collusion olanları al
test_idx = y_test[y_test == 1].index
df_test_coll = df.loc[test_idx]
X_coll = df_test_coll.drop(columns=["shop_id", "is_collusion", "collusion_group"])
y_group = df_test_coll["collusion_group"]

# Yalnızca collusion grubu tahmini için model eğit
df_train_coll = df[df["is_collusion"] == 1]
X_train_group = df_train_coll.drop(columns=["shop_id", "is_collusion", "collusion_group"])
y_train_group = df_train_coll["collusion_group"]

clf_group = RandomForestClassifier(random_state=42)
clf_group.fit(X_train_group, y_train_group)

# Grup tahmini yap
y_pred_group = clf_group.predict(X_coll)

# Değerlendir
print("\n[2] Collusion Group Classification")
labels = sorted(y_group.unique())
print(classification_report(y_group, y_pred_group, digits=4))
cm_group = confusion_matrix(y_group, y_pred_group, labels=labels)
plot_confusion_matrix(cm_group, labels, "Confusion Matrix - Collusion Groups")
