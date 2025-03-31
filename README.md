# Final Project - Manufacturer & Distributor Management System

## 📋 Project Description
This project is a **Manufacturer and Distributor Management System**, built using **Python** and integrated with a **MongoDB database**. The system allows users to:
- Dynamically manage manufacturers and distributors.
- Handle multiple products, prices, and descriptions efficiently.
- Track and update products across different collections.

The project can calculate profit margins for manufacturers and distributors and ensures seamless handling of new products and historical data.

---

## 🚀 Features
- **Dynamic Product Handling**: Supports adding and updating multiple products with their prices and descriptions.
- **Profit Calculation**: Automatically adds profit margins for manufacturers and distributors.
- **Efficient Updates**: Ensures all existing and new products are updated without breaking the database structure.
- **MongoDB Integration**: Connects to a MongoDB Atlas instance for robust data storage and retrieval.
- **Error Handling**: Gracefully handles cases where products are missing prices for specific dates.

---

## 🛠️ Installation

### Prerequisites
1. Python 3.11 or later.
2. A MongoDB Atlas account. You can sign up [here](https://www.mongodb.com/cloud/atlas).
3. Install the required Python libraries:
pip install pymongo
pip install yfinance



### Steps
1. Clone the repository:
   git clone https://github.com/emreanalan/MongoDBProject.git
2. Create a **MongoDB cluster** and add your database connection string in the code.
3. Run the scripts (python files) to manage your data.

---

## 📝 How to Use

### Project Steps

#### 1. Fetching Raw Material Data into the Database
In this step, data for minimum wage, electricity, and natural gas over one year was collected using **web scraping** via `SELENIUM`. You can find the related code in the following files:
- `asgari.py`
- `electric.py`
- `dogalgaz.py`

For raw materials and metals, I utilized Python's `YFINANCE` library to retrieve data spanning over a year. The algorithm is implemented in the `AL_GD_Cop_EUR_USD_Petrol.py` file. This script works in two modes:
1. **Historical Data Validation**: Checks all historical dates to ensure no dates are missing and adds any skipped dates.
2. **Updating with Recent Data**: Fetches data from the last recorded date up to today and updates the database.

Additionally, since markets are closed on weekends, data for those days would be missing. To address this, the script fills in the missing weekend data by using the values from the most recent previous working day. This ensures no gaps remain in the database.

---

#### 2. Creating Product Models and Product Database
Using the collected raw material data, this step calculates the **daily costs** of a product and stores the data in the database. The implemented method allows for easy material specification and automatic computation of daily costs.

The function `insert_daily_costs("MyToy", materials)` is used to calculate the daily costs of a product named "MyToy" and insert them into the database.

---

#### 3. Creating Production, Manufacturer, and Distributor Databases
With the `Production.py` file:
- You can define the materials used for a product.
- Generate a product using annual price data for all materials.
- Store details such as the product's date, cost, and materials in the database.

With the `Manufacturer.py` and `Distributor.py` files:
- You can associate profit margins with manufacturers and distributors.
- Profit margins can be applied on a **daily basis** and over customizable date ranges.
- This enables tracking the entire production and distribution process, with profitability.

---

#### 4. Adding Shops and Special Profit Makers to the Database
- **`Shop.py`**: Represents example shopping firms in Türkiye. These firms can list products for sale, specifying the manufacturers they buy from and the profit percentages they apply.
- Firms can work with **multiple manufacturers** to sell various products, as seen in the database examples.
  
- **`Cheater.py`**: Enables firms to sell products with a higher profit margin. This script supports:
  1. Applying additional profit margins to specific products from specific manufacturers.
  2. Applying a general profit margin to all products supplied by specific manufacturers.

---

#### 5. Final Enhancements to the Database
- **Production Rates**: Allows defining production levels as low, medium, or high for manufacturers and adjusts profits accordingly.
- **Collusion Algorithms**: Implements leader-follower markets using `CollusionShop.py`. Features include:
  - Assigning a leader market and follower markets with delay parameters.
  - Adding fallback values for missed dates to ensure accurate profit allocation.

- **Cheater Function**: For firms applying extra profits.
- **Non-Collusion Functions**: Creates markets using max, min, and average values without collusion.
- **Maverick Markets**: Generates independent markets with unique prices unrelated to others.

Example Usage:
- For production rate adjustments:
  ```python
  db_manufacturer("ManufacturerA", "MyCar", production_rate="high")  # Production rate of 'high' adjusts profit accordingly
- For collusion-based markets:
  collusion_shop("LeaderShop", "ManufacturerA", 20, delay=2, fallback_date="2023-11-01", followers=["FollowerShop1", "FollowerShop2"])

