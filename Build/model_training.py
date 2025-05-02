import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def train_model(input_csv, test_size=0.3, random_state=42):
    # Veriyi yükle
    df = pd.read_csv(input_csv)

    # Özellikleri ve etiketleri ayır
    X = df.drop(columns=["Shop", "Label"])
    y = df["Label"]

    # Eğitim/test ayır
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Modeli oluştur ve eğit
    clf = RandomForestClassifier(n_estimators=100, random_state=random_state)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    # Performans raporu
    print("🔍 Model Performans Raporu:")
    print(classification_report(y_test, y_pred))

    # Özellik önemleri
    feature_importances = clf.feature_importances_
    feature_names = X.columns
    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": feature_importances
    }).sort_values(by="Importance", ascending=False)

    print("\n🔎 Özellik Önem Sıralaması:")
    print(importance_df)

    # Görselleştirme
    plt.figure(figsize=(10, 6))
    plt.barh(importance_df["Feature"], importance_df["Importance"], color="skyblue")
    plt.gca().invert_yaxis()
    plt.title("🔍 Feature Importance (Random Forest)")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.show()

    return clf

# --- Kullanım Örneği ---
if __name__ == "__main__":
    train_model("C:/Users/emrea/Desktop/FINAL PROJECT/MongoDBProject/utils/shop_features_labeled.csv")
