from PySide6.QtCore import QObject, Slot, Property, QStringListModel, Signal, QThread
from datetime import datetime, timedelta
import sys
import os
from QTSynchronizers.Workers.ShopLoaderWorker import ShopLoaderWorker
# Build klasöründen import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Build')))
from DataRetrieval import fetch_all_manufacturers, fetch_shops_for_manufacturer

class ProfitCalculationQTSynchronizer(QObject):
    closePopup = Signal()
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
        manufacturers = fetch_all_manufacturers()
        print("Loaded manufacturers:", manufacturers)
        self._manufacturerModel.setStringList(manufacturers)

    @Slot(str)
    def loadShopsForManufacturer(self, manufacturer_name):
        self._shopModel.setStringList([])  # Temizle

        # Yeni Worker oluştur
        self._worker = ShopLoaderWorker(manufacturer_name)
        self._worker_thread = QThread()

        self._worker.moveToThread(self._worker_thread)

        # Bağlantılar
        self._worker.shopsLoaded.connect(self._onShopsLoaded)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        # İş bitince popup kapatma
        self._worker.finished.connect(self._onWorkerFinished)

        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    @Slot()
    def goBackToMainMenu(self):
        if self.profitCalculation_window:
            print("Hiding profit window...")
            self.profitCalculation_window.hide()
        if self.main_window:
            print("Showing main window...")
            self.main_window.show()
    @Slot(str)
    def appendOutput(self, line):
        lines = self._outputModel.stringList()
        lines.append(line)
        self._outputModel.setStringList(lines)

    @Slot()
    def clearOutput(self):
        self._outputModel.setStringList([])


    @Slot(list)
    def _onShopsLoaded(self, shop_list):
        print(f"Fetched shops: {shop_list}")
        self._shopModel.setStringList(shop_list)

    @Slot()
    def _onWorkerFinished(self):
        self.closePopup.emit()

    # Diğer hesaplama fonksiyonları buraya eklenecek (örneğin showGeneralStats, calculateProfitForShop vs.)