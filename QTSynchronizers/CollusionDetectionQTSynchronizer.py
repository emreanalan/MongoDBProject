# QTSynchronizers/CollusionDetectionQTSynchronizer.py

from PySide6.QtCore import QObject, Slot, Property, QStringListModel, QThread
from QTSynchronizers.Workers.CollusionWorker import CollusionWorker

class CollusionDetectionQTSynchronizer(QObject):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self._outputLines = []  # Text satırlarını tutar
        self._outputModel = QStringListModel()  # QML tarafına bağlanacak model

        self.main_window = None
        self.collusion_window = None

        self.worker = None
        self.worker_thread = None

    @Property(QObject, constant=True)
    def outputModel(self):
        """
        QML tarafına model olarak sunulan liste modeli
        """
        return self._outputModel

    @Slot(str, str)
    def detectCollusion(self, start_date, end_date):
        """
        Detect Collusion butonuna basıldığında çalışır.
        """
        print("Detecting collusion...")

        # Önce eski sonuçları temizle
        self._outputLines.clear()
        self._outputModel.setStringList([])

        # Yeni worker oluştur
        self.worker = CollusionWorker(start_date, end_date)
        self.worker_thread = QThread()

        # Worker'ı kendi thread'ine taşı
        self.worker.moveToThread(self.worker_thread)

        # Worker sinyallerini bağla
        self.worker.newOutput.connect(self.appendOutput)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        # İşlem bittiğinde ek iş yapılacaksa (örneğin popup kapama)
        self.worker.finished.connect(self._onWorkerFinished)

        # Thread çalışınca worker başlasın
        self.worker_thread.started.connect(self.worker.run)

        # Thread başlat
        self.worker_thread.start()

    @Slot(str)
    def appendOutput(self, line):
        """
        Worker'dan gelen her yeni satırı modele ekler.
        """
        self._outputLines.append(line)
        self._outputModel.setStringList(self._outputLines)

    @Slot()
    def goBackToMainMenu(self):
        """
        Ana Menüye dönüş butonu için çalışır.
        """
        print("Going back to Main Menu")

        if self.collusion_window:
            print("Hiding collusion window...")
            self.collusion_window.hide()

        if self.main_window:
            print("Showing main window...")
            self.main_window.show()

    @Slot()
    def _onWorkerFinished(self):
        self.closePopup.emit()