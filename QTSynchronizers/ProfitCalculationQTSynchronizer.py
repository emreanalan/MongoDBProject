# QTSynchronizers/ProfitCalculationQTSynchronizer.py

from PySide6.QtCore import QObject, Slot, Property, QStringListModel
from datetime import datetime, timedelta
import sys
import os

# Build klasöründen import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Build')))
from DataRetrieval import fetch_all_manufacturers, fetch_shops_for_manufacturer

class ProfitCalculationQTSynchronizer(QObject):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self._manufacturerModel = QStringListModel()
        self._shopModel = QStringListModel()
        self._outputModel = QStringListModel()

        self.main_window = None
        self.profit_window = None

    # === MODELLER ===

    @Property(QObject, constant=True)
    def manufacturerModel(self):
        return self._manufacturerModel

    @Property(QObject, constant=True)
    def shopModel(self):
        return self._shopModel

    @Property(QObject, constant=True)
    def outputModel(self):
        return self._outputModel

    # === BAŞLANGIÇ FONKSİYONLARI ===

    @Slot()
    def loadManufacturers(self):
        print("Loading manufacturers...")
        manufacturers = fetch_all_manufacturers()
        self._manufacturerModel.setStringList(manufacturers)

    @Slot()
    def loadUniqueShops(self):
        """
        Tüm manufacturerlardan tüm shop'ları çekip, unique liste oluşturur ve alfabetik sıraya dizer.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        print("Fetching all unique shops...")

        all_shops = []

        manufacturers = fetch_all_manufacturers()
        print(f"Found manufacturers: {manufacturers}")

        for manu in manufacturers:
            try:
                shops = fetch_shops_for_manufacturer(manu) or []
                all_shops.extend(shops)
                print(f"Shops found for {manu}: {shops}")
            except Exception as e:
                print(f"Error fetching shops for {manu}: {e}")

        # Unique ve sıralı hale getir
        unique_shops = sorted(list(set(all_shops)))

        print(f"Unique sorted shops: {unique_shops}")

        self._shopModel.setStringList(unique_shops)
        if not unique_shops:
            print("⚠️ No shops found in the database!")



