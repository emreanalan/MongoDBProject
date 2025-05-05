import pandas as pd
import joblib
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

# 📌 MODEL DOSYALARI
bin_model_path = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Models/model_binary.pkl"
grp_model_path = "C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Models/model_group.pkl"

# 📁 YENİ VERİ SETİ (100 shop)
df_test = pd.read_csv("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/Build/Cvss/shop_features2.csv")

# 🧩 Kullanılacak özellikler (eğitimdeki ile birebir aynı olmalı)
features = [
    "avg_profit_pct", "profit_pct_std", "avg_profit_similarity"
]
X_test = df_test[features]

# 📦 Modelleri yükle
clf_bin = joblib.load(bin_model_path)
clf_grp = joblib.load(grp_model_path)

# 🕵️‍♂️ Binary Collusion Tahmini
df_test["pred_binary"] = clf_bin.predict(X_test)

# ✅ Detected Collusion Shops
collusion_shops = df_test[df_test["pred_binary"] == 1]

# 🧠 Grup Tahmini (Sadece collusion olduğu tahmin edilenler)
X_group = collusion_shops[features]
group_preds = clf_grp.predict(X_group)
df_test.loc[df_test["pred_binary"] == 1, "predicted_group"] = group_preds

# 🔍 Eğer gerçek grup etiketleri varsa, performansı ölç
if "label_group" in df_test.columns:
    y_true = collusion_shops["label_group"]
    y_pred = group_preds
    print("\n📊 Collusion Group Classification Report:")
    print(classification_report(y_true, y_pred, zero_division=0))

cm = confusion_matrix(y_true, y_pred, labels=sorted(y_true.unique()))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix - Collusion Group (Test Set)")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()
