from PySide6.QtCore import QObject, Signal, Slot
import sys
import os

# Build dizinini içeri aktarılabilir hale getiriyoruz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'Build')))
from DataRetrieval import fetch_shops_for_manufacturer

class ShopLoaderWorker(QObject):
    shopsLoaded = Signal(list)
    finished = Signal()

    def __init__(self, manufacturer):
        super().__init__()
        self.manufacturer = manufacturer

    @Slot()
    def run(self):
        try:
            print(f"[Worker] Fetching shops for {self.manufacturer}...")
            shops = fetch_shops_for_manufacturer(self.manufacturer) or []
            print(f"[Worker] Shops fetched: {shops}")
            self.shopsLoaded.emit(shops)
        except Exception as e:
            print(f"[Worker] Error fetching shops: {e}")
            self.shopsLoaded.emit([])  # Hata durumunda boş liste döndür
        self.finished.emit()
