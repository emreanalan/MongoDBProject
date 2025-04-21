from PySide6.QtCore import QObject, Slot, QUrl
import os

class Backend(QObject):
    def __init__(self, engine, dynamicHandler):
        super().__init__()
        self.engine = engine
        self.dynamicHandler = dynamicHandler
        self.main_window = None
        self.feature_windows = {}

    @Slot(int)
    def selectFeature(self, feature_id):
        print(f"Selected feature ID: {feature_id}")

        if self.main_window:
            self.main_window.hide()

        if feature_id not in self.feature_windows:
            # Eğer o feature daha yüklenmemişse, yükle
            self.loadFeatureWindow(feature_id)

        feature_window = self.feature_windows.get(feature_id)
        if feature_window:
            feature_window.show()

    @Slot()
    def goBackToMainMenu(self):
        print("Going back to Main Menu")

        for fw in self.feature_windows.values():
            fw.hide()

        if self.main_window:
            self.main_window.show()


    def loadFeatureWindow(self, feature_id):
        qml_file_map = {
            1: "DynamicProductHandling.qml",
            4: "CollusionDetection.qml"
        }

        qml_filename = qml_file_map.get(feature_id)
        if not qml_filename:
            print(f"Feature {feature_id} için QML bulunamadı.")
            return

        qml_path = os.path.join(os.path.dirname(__file__), "..", "UI", qml_filename)
        self.engine.load(QUrl.fromLocalFile(os.path.abspath(qml_path)))

        roots = self.engine.rootObjects()
        if roots:
            new_window = roots[-1]
            self.feature_windows[feature_id] = new_window
            print(f"Feature {feature_id} başarıyla yüklendi.")

            if feature_id == 1:
                self.dynamicHandler.dynamic_window = new_window
            if feature_id == 4:
                self.dynamicHandler.dynamic_window = new_window



