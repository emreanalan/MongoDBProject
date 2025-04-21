from PySide6.QtCore import QObject, Slot

class Backend(QObject):
    def __init__(self):
        super().__init__()

    @Slot(int)
    def selectFeature(self, feature_id):
        print(f"Selected feature ID: {feature_id}")
        # İleride burada feature sayfasına geçiş yapacağız
