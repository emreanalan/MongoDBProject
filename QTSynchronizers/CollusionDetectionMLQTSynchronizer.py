# QTSynchronizers/CollusionDetectionMLQTSynchronizer.py

from PySide6.QtCore import QObject, Slot, Property, QStringListModel
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
)

class CollusionDetectionMLQTSynchronizer(QObject):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self._outputLines = []
        self._outputModel = QStringListModel()

        self.main_window = None
        self.ml_window = None

    @Property(QObject, constant=True)
    def outputModel(self):
        return self._outputModel

    @Slot()
    def runModel(self):
        print("⚙️ ML tabanlı collusion detection modeli çalıştırılıyor...")

        self._outputLines.clear()
        self._outputModel.setStringList([])

        try:
            df = pd.read_csv("Build/Cvss/shop_features2.csv")
            df = df.drop(columns=['shop_id'])

            X = df.drop(columns=['is_collusion', 'collusion_group'])
            y = df['collusion_group']

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            accuracy = accuracy_score(y_test, y_pred)
            ari = adjusted_rand_score(y_test, y_pred)
            nmi = normalized_mutual_info_score(y_test, y_pred)

            self.appendOutput(f"✅ Accuracy: {accuracy:.4f}")
            self.appendOutput(f"✅ Adjusted Rand Index (ARI): {ari:.4f}")
            self.appendOutput(f"✅ Normalized Mutual Information (NMI): {nmi:.4f}")
            self.appendOutput("")

            self.appendOutput("📋 Classification Report:")
            report = classification_report(y_test, y_pred, zero_division=0)
            for line in report.splitlines():
                self.appendOutput(line.strip())

            print("✅ ML modeli başarıyla çalıştı.")
        except Exception as e:
            self.appendOutput(f"❌ Hata oluştu: {str(e)}")

    @Slot(str)
    def appendOutput(self, line):
        self._outputLines.append(line)
        self._outputModel.setStringList(self._outputLines)

    @Slot()
    def goBackToMainMenu(self):
        print("Ana menüye dönülüyor...")
        if self.ml_window:
            self.ml_window.hide()
        if self.main_window:
            self.main_window.show()
