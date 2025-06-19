import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

from QTSynchronizers.MainMenuQTSynchronizer import Backend
from QTSynchronizers.DynamicProductHandlingQTSynchronizer import DynamicProductHandlingQTSynchronizer
from QTSynchronizers.CollusionDetectionQTSynchronizer import CollusionDetectionQTSynchronizer
from QTSynchronizers.ProfitCalculationQTSynchronizer import ProfitCalculationQTSynchronizer
from QTSynchronizers.FraudDetectionQTSynchronizer import FraudDetectionQTSynchronizer
from QTSynchronizers.CollusionDetectionMLQTSynchronizer import CollusionDetectionMLQTSynchronizer

app = QApplication(sys.argv)
engine = QQmlApplicationEngine()

# Dynamic Handler: DynamicProductHandling işlemleri için
dynamicHandler = DynamicProductHandlingQTSynchronizer(engine)
collusionHandler = CollusionDetectionQTSynchronizer(engine)
FraudHandler = FraudDetectionQTSynchronizer(engine)
profitCalculationHandler = ProfitCalculationQTSynchronizer(engine)
mlHandler = CollusionDetectionMLQTSynchronizer(engine)

# Backend Handler: Ana menü kontrolü
backend = Backend(engine, dynamicHandler, collusionHandler, FraudHandler, profitCalculationHandler, mlHandler)

# QML'den erişebileceğimiz contextProperty'ler
engine.rootContext().setContextProperty("backend", backend)
engine.rootContext().setContextProperty("dynamicHandler", dynamicHandler)
engine.rootContext().setContextProperty("collusionHandler", collusionHandler)
engine.rootContext().setContextProperty("FraudHandler", FraudHandler)
engine.rootContext().setContextProperty("profitCalculationHandler", profitCalculationHandler)
engine.rootContext().setContextProperty("mlHandler", mlHandler)


# Ana Menü QML yükle
qml_file = os.path.join(os.path.dirname(__file__), "UI", "MainMenu.qml")
engine.load(QUrl.fromLocalFile(os.path.abspath(qml_file)))

if not engine.rootObjects():
    print("Ana Menü yüklenemedi!")
    sys.exit(-1)

backend.main_window = engine.rootObjects()[0]
dynamicHandler.main_window = backend.main_window  # DynamicHandler ana pencereyi bilsin
collusionHandler.main_window = backend.main_window
FraudHandler.main_window = backend.main_window
profitCalculationHandler.main_window = backend.main_window


sys.exit(app.exec())
