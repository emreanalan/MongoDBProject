from PySide6.QtCore import QObject, Slot, Property, QStringListModel, QThread, Signal
from QTSynchronizers.Workers.FraudWorker import MLFraudWorker, RuleFraudWorker

class FraudDetectionQTSynchronizer(QObject):
    closePopup = Signal()  # QML'deki popup'u kapatmak için sinyal

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self._outputLines = []
        self._outputModel = QStringListModel()

        self.main_window = None
        self.fraud_window = None

        self.worker = None
        self.worker_thread = None

    @Property(QObject, constant=True)
    def outputModel(self):
        return self._outputModel

    @Slot(str, str)
    def detectMLFraud(self, start_date, end_date):
        self._startWorker(MLFraudWorker(start_date, end_date))

    @Slot(str, str, str)
    def detectRuleFraud(self, start_date, end_date, max_profit):
        self._startWorker(RuleFraudWorker(start_date, end_date, max_profit))

    def _startWorker(self, worker):
        self._outputLines.clear()
        self._outputModel.setStringList([])

        self.worker = worker
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker.newOutput.connect(self.appendOutput)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.finished.connect(self._onWorkerFinished)

        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    @Slot(str)
    def appendOutput(self, line):
        self._outputLines.append(line)
        self._outputModel.setStringList(self._outputLines)

    @Slot()
    def _onWorkerFinished(self):
        self.closePopup.emit()

    @Slot()
    def goBackToMainMenu(self):
        if self.fraud_window:
            self.fraud_window.hide()
        if self.main_window:
            self.main_window.show()
