from PySide6.QtCore import QObject, Slot, Property, QStringListModel, Signal, QThread
from datetime import datetime, timedelta
import sys
import os
import io
import base64
import pandas as pd
from PySide6.QtGui import QImage
from PySide6.QtCore import QBuffer, QByteArray
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from QTSynchronizers.Workers.ShopLoaderWorker import ShopLoaderWorker
from QTSynchronizers.Workers.ProductLoaderWorker import ProductLoaderWorker
# Build klasöründen import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Build')))
from DataRetrieval import fetch_all_manufacturers, fetch_price_data_from_shop, fetch_shops_for_manufacturer

class ProfitCalculationQTSynchronizer(QObject):
    closePopup = Signal()

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

        self._manufacturerModel = QStringListModel()
        self._shopModel = QStringListModel()
        self._productModel = QStringListModel()
        self._outputModel = QStringListModel()

        self.main_window = None
        self.profit_window = None

    # === MODELLER ===
    @Property(QObject, constant=True)
    def productModel(self):
        return self._productModel

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
    def loadShopsForManufacturer(self, manufacturer):
        self._shopModel.setStringList([])

        self._worker = ShopLoaderWorker(manufacturer)
        self._worker_thread = QThread()

        self._worker.moveToThread(self._worker_thread)

        self._worker.shopsLoaded.connect(self._onShopsLoaded)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

    @Slot(list)
    def _onShopsLoaded(self, shop_list):
        self._shopModel.setStringList(shop_list)
        print(f"Fetched shops: {shop_list}")
        self.closePopup.emit()

    @Slot(str, str, str, str)
    def drawPriceChartForShop(self, start_date, end_date, shop_name, manufacturer_name):
        self.appendOutput(f"⏳ Drawing price chart for {shop_name} and {manufacturer_name}...")

        df = fetch_price_data_from_shop(shop_name, manufacturer_name, start_date, end_date)

        if df.empty:
            self.appendOutput("⚠️ No data found to draw chart.")
            self.closePopup.emit()
            return

        if 'product_name' not in df.columns:
            self.appendOutput("⚠️ Product info not found in data.")
            self.closePopup.emit()
            return

        plt.figure(figsize=(12, 5))

        for product in df['product_name'].unique():
            df_prod = df[df['product_name'] == product]
            plt.plot(df_prod['date'], df_prod['price'], label=product)

        plt.title(f"Price History for {shop_name} ({manufacturer_name}) - by Product")
        plt.xlabel("Date")
        plt.ylabel("Price (TL)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        from io import BytesIO
        import base64
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        data_url = f"data:image/png;base64,{encoded}"

        self.engine.rootContext().setContextProperty("chartImagePath", data_url)
        self.closePopup.emit()

    @Slot(str, str, str, str)
    def calculateProfitForShop(self, start_date, end_date, manufacturer, shop):
        self.clearOutput()
        self.appendOutput(f"📊 Calculating profit for Shop: {shop} and Manufacturer: {manufacturer}...")
        self.drawPriceChartForShop(start_date, end_date, shop, manufacturer)
        # İleride buraya ek analiz metinleri/çıktıları da eklenebilir

    @Slot(str, str, str)
    def calculateProfitForManufacturer(self, start_date, end_date, manufacturer):
        self.clearOutput()
        self.appendOutput(f"📊 Drawing shop-level average product prices for {manufacturer}...")

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        shop_list = fetch_shops_for_manufacturer(manufacturer)
        if not shop_list:
            self.appendOutput("⚠️ No shops found for this manufacturer.")
            self.closePopup.emit()
            return

        combined_df = pd.DataFrame()

        for shop in shop_list:
            df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
            if df.empty or 'product_name' not in df.columns:
                continue
            df['shop'] = shop
            df['date'] = pd.to_datetime(df['date'])
            grouped = df.groupby('date')['price'].mean().reset_index()
            grouped['shop'] = shop
            combined_df = pd.concat([combined_df, grouped], ignore_index=True)

        if combined_df.empty:
            self.appendOutput("⚠️ No price data available for this manufacturer.")
            self.closePopup.emit()
            return

        # === ÇİZGİ GRAFİK ===
        plt.figure(figsize=(12, 5))
        for shop in combined_df['shop'].unique():
            df_shop = combined_df[combined_df['shop'] == shop]
            plt.plot(df_shop['date'], df_shop['price'], label=shop)

        plt.title(f"Daily Avg Product Prices by Shop ({manufacturer})")
        plt.xlabel("Date")
        plt.ylabel("Average Price (TL)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        # Encode as base64 to avoid saving to file
        from io import BytesIO
        import base64
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        data_url = f"data:image/png;base64,{encoded}"

        self.engine.rootContext().setContextProperty("chartImagePath", data_url)
        self.appendOutput("✅ Chart updated successfully.")
        self.closePopup.emit()

    @Slot(str, str)
    def loadProductsForShop(self, manufacturer, shop):
        self._productModel.setStringList([])

        self._product_worker = ProductLoaderWorker(manufacturer, shop)
        self._product_worker_thread = QThread()

        self._product_worker.moveToThread(self._product_worker_thread)
        self._product_worker.productsLoaded.connect(self._onProductsLoaded)
        self._product_worker.finished.connect(self._product_worker_thread.quit)
        self._product_worker.finished.connect(self._product_worker.deleteLater)
        self._product_worker_thread.finished.connect(self._product_worker_thread.deleteLater)

        self._product_worker_thread.started.connect(self._product_worker.run)
        self._product_worker_thread.start()

    @Slot(list)
    def _onProductsLoaded(self, product_list):
        self._productModel.setStringList(product_list)
        print(f"Fetched products: {product_list}")
        self.closePopup.emit()

    @Slot(str, str, str, str, str)
    def showProductStats(self, start_date, end_date, manufacturer, shop, product):
        self.clearOutput()
        self.appendOutput(f"📊 Drawing price trend for '{product}'...")

        df = fetch_price_data_from_shop(shop, manufacturer, start_date, end_date)
        df = df[df['product_name'] == product]
        if df.empty:
            self.appendOutput(f"⚠️ No data found for product '{product}'")
            self.closePopup.emit()
            return

        df = df.sort_values("date")

        # Grafik çizimi
        plt.figure(figsize=(10, 4))
        plt.plot(df["date"], df["price"], marker="o", linestyle="-", color="steelblue", label=product)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gcf().autofmt_xdate()
        plt.title(f"{product} Price Trend")
        plt.xlabel("Date")
        plt.ylabel("Price (TL)")
        plt.grid(True)
        plt.tight_layout()

        # Grafik base64 olarak encode edilir
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_data = buf.read()
        buf.close()
        plt.close()

        encoded = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:image/png;base64,{encoded}"
        self.engine.rootContext().setContextProperty("chartImagePath", data_url)

        self.appendOutput("✅ Product chart updated successfully.")
        self.closePopup.emit()

    @Slot()
    def goBackToMainMenu(self):
        if self.profitCalculation_window:
            self.profitCalculation_window.hide()
        if self.main_window:
            self.main_window.show()

    @Slot(str)
    def appendOutput(self, line):
        lines = self._outputModel.stringList()
        lines.append(line)
        self._outputModel.setStringList(lines)

    @Slot()
    def clearOutput(self):
        self._outputModel.setStringList([])