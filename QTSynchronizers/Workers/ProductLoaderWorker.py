# QTSynchronizers/Workers/ProductLoaderWorker.py

from PySide6.QtCore import QObject, Signal, Slot
import sys
import os

# Build dizinini içeri aktarılabilir hale getiriyoruz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'Build')))
from DataRetrieval import fetch_products_for_shop  # Yeni hali: (manufacturer_name, shop_name)

class ProductLoaderWorker(QObject):
    productsLoaded = Signal(list)
    finished = Signal()

    def __init__(self, manufacturer_name, shop_name):
        super().__init__()
        self.manufacturer_name = manufacturer_name
        self.shop_name = shop_name

    @Slot()
    def run(self):
        try:
            print(f"[Worker] Fetching products for {self.shop_name} - {self.manufacturer_name}...")
            products = fetch_products_for_shop(self.manufacturer_name, self.shop_name)
            print(f"[Worker] Products fetched: {products}")
            self.productsLoaded.emit(products)
        except Exception as e:
            print(f"[Worker] Error fetching products: {e}")
            self.productsLoaded.emit([])

        self.finished.emit()
