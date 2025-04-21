import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl, QObject

from QTSynchronizers.backend import Backend

if __name__ == "__main__":
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    qml_file = os.path.join(os.path.dirname(__file__), "ui", "main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))

    if not engine.rootObjects():
        print("QML load failed.")
        sys.exit(-1)

    # Main window için kapanış kontrolü
    window = engine.rootObjects()[0]
    window.destroyed.connect(app.quit) # <-- bu satırı ekle!

    sys.exit(app.exec())
