from PySide6.QtCore import QObject, Slot, Property, QStringListModel
from datetime import datetime, timedelta
import sys
import os

# DataRetrieval dosyasını Build klasöründen çekiyoruz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Build')))
from DataRetrieval import fetch_all_manufacturers, fetch_manufacturer_data, fetch_shops_for_manufacturer, fetch_all_manufacturers
from Production import insert_daily_costs

class DynamicProductHandlingQTSynchronizer(QObject):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self._productListModel = QStringListModel()

        self.main_window = None        # Ana menü penceresini tutacağız
        self.dynamic_window = None     # Dynamic Product Handling penceresini tutacağız

    @Property(QObject, constant=True)
    def productListModel(self):
        return self._productListModel

    @Slot()
    def loadProducts(self):
        """
        Son 3 ayın ürünlerini otomatik olarak çeker ve listeyi günceller.
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        print(f"Fetching products between {start_str} and {end_str}...")

        manufacturers = fetch_all_manufacturers()
        all_products = []

        for manu in manufacturers:
            manu_df = fetch_manufacturer_data(manu, start_str, end_str)
            if not manu_df.empty:
                product_names = manu_df['product_name'].unique().tolist()
                all_products.extend(product_names)

        all_products = list(set(all_products))  # Duplicate'ları temizle

        print("Fetched Products List:")
        for product in all_products:
            print("-", product)

        print(f"Total unique products fetched: {len(all_products)}")

        self._productListModel.setStringList(all_products)

    @Slot()
    def goBackToMainMenu(self):
        print("Going back to Main Menu")

        # Dynamic window'ı gizle
        if self.dynamic_window:
            print("Hiding dynamic window...")
            self.dynamic_window.hide()

        # Ana menüyü göster
        if self.main_window:
            print("Showing main window...")
            self.main_window.show()

    @Slot()
    def loadManufacturers(self):
        print("Fetching all manufacturers...")
        manufacturers = fetch_all_manufacturers()
        manufacturers = list(set(manufacturers))
        self._productListModel.setStringList(manufacturers)
        print(f"Fetched manufacturers: {manufacturers}")

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

        self._productListModel.setStringList(unique_shops)

    @Slot("QVariantMap")
    def createProduct(self, product_name, material_dict):
        print("Creating product with materials:")
        for key, value in material_dict.items():
            print(f"  {key}: {value}")

        # Burada kullanıcıdan ürün adı isteyebilirsin (şimdilik örnek):
        product_name = "Custom_Product"

        # insert_daily_costs fonksiyonu çağrılıyor
        insert_daily_costs(product_name, material_dict)

        print(f"Product '{product_name}' successfully inserted.")

