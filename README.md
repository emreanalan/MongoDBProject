# MongoDB Manufacturer & Distributor Management System

> **Author:** Rauf Emre Analan  
> **Project Type:** Manufacturer, Distributor, and Market Behavior Management  
> **Database:** MongoDB  
> **Language:** Python  

---

## 📋 Project Overview

This project is a **Manufacturer and Distributor Management System** integrated with **dynamic market behavior detection** features such as **Collusion Detection** and **Fraud Detection**. It allows users to dynamically manage manufacturers, distributors, products, and shops while analyzing price trends, profit margins, and market behaviors over time.

Built on top of Python and MongoDB, the system ensures a scalable, flexible, and real-world applicable environment for supply chain analysis, profit tracking, market monitoring, and collusion detection.

---

## 🚀 Key Features

- **Dynamic Product Handling:** Efficiently add, update, and track multiple products and raw materials.
- **Profit Calculation:** Calculates and manages daily profit margins for manufacturers and distributors.
- **Shop Management:** Simulates real-world shopping markets including profit assignments and fraudulent behaviors.
- **Collusion Detection:** Identifies leader-follower behaviors and price-fixing patterns with fallback options.
- **Fraud Detection:** Detects anomalies and shops applying extra profits.
- **Production Rates:** Adjust profit margins based on production scale (low, medium, high).
- **Feature Engineering:** Prepares datasets for model training and shop behavior classification.
- **Model Training:** Machine learning integration for future prediction and anomaly scoring.
- **Historical Data Management:** Handles missing data smartly by interpolating weekend or holiday gaps.
- **Fully Integrated UI:** Interactive front-end that presents every module in a visual and accessible way.

---

## 🛠️ Prerequisites

- **Python 3.11+**
- **MongoDB Atlas Account** (or local MongoDB instance)
- Python Libraries:
  - `pymongo`
  - `yfinance`
  - `selenium`
  - `scikit-learn`
  - `pandas`
  - `numpy`
  - `matplotlib`

You can install the libraries using:

```bash
pip install pymongo yfinance selenium scikit-learn pandas numpy matplotlib
```

---

## 🏗️ Project Structure

```
MongoDBProject/
├── build/
│   ├── Al_GD_Cop_fetching.py
│   ├── EUR_TRY_Fetching.py
│   ├── Others_Fetching.py
│   ├── asgari.py
│   ├── electric.py
│   ├── dogalgaz.py
│   ├── Cheater.py
│   ├── CheaterWithDateInterval.py
│   ├── CollusionDetection.py
│   ├── CollusionShop.py
│   ├── NewCollusionShop.py
│   ├── DataRetrieval.py
│   ├── DataUpdater.py
│   ├── DeleteData.py
│   ├── Distributor.py
│   ├── Manufacturer.py
│   ├── MongoDbConnect.py
│   ├── Production.py
│   ├── ProductsCollection.py
│   ├── Shops.py
│   ├── Shop.py
│   ├── FastUpdateMan.py
│   ├── FraudDetection.py
│   ├── FraudDetectionWithProfit.py
│   ├── FeatureEngineering.py
│   ├── ShopFeatureEngineering.py
│   ├── ModelTraining.py
│   ├── Utils.py
│   ├── Tests.py
├── README.md                        
```

---

## 📝 How to Use

### 1. Fetching Raw Material Data
- `Al_GD_Cop_fetching.py`, `EUR_TRY_Fetching.py`, `Others_Fetching.py`

**Note:** Weekend/holiday gaps are automatically filled.

### 2. Product Model Creation
- `ProductionCollection.py`
- Use `insert_daily_costs()` to insert costs into the database.
-![Main Menu](./csv_yedek/ProductMongoDB.jpeg)
### 3. Manufacturer & Distributor Databases
- `Manufacturer.py` and `Distributor.py`
-![Main Menu](./csv_yedek/Manufacturer%20dataset.png)
### 4. Shops and Market Simulation
- `RandomShopGenerator.py`
- `Cheater.py`, `CheaterWithDateInterval.py`
-![Main Menu](./csv_yedek/Product244%20-%20Collusion%20Shops.png)
### 5. Collusion & Fraud Detection
- `CollusionDetection.py`, `CollusionShop.py`, `NewCollusionShop.py`
- `FraudDetection.py`, `FraudDetectionWithProfit.py`

### 6. Feature Engineering & Model Training
- `featureEngineering.py`, `ShopFeatureEngineering.py`
- `ModelTraining.py`
-![Main Menu](./csv_yedek/ModelTrainingFeature.png)
---

## 🔍 How do we produce collusion shops?
Collusion shops are generated using a controlled simulation process where **multiple shops are designed to follow similar pricing behaviors**, simulating a coordinated pricing cartel. Here's how the generation works internally:

### 🏗 Group Structure:
- A set of shops are grouped into a collusion group (e.g., 10 shops per group).
- Each group shares **common manufacturers** and a set of **target collusion products**.

### 🛠 Price Simulation Process:
- **Collusion Profit Margins** are predefined for selected products (e.g., 8%–12%).
- **Zam (price raise) Days** are selected for each group.
- Each shop has a small **delay offset (0–4 days)** relative to the group leader shop.
- Shops apply the same zam % at staggered times, mimicking delay-based coordination.
- A small **random deviation (sapma)** is applied per shop to avoid perfect overlap.

### 🧾 Implementation Summary:
- On zam days:
  ```python
  new_price = old_price * (1 + zam_orani)
  new_price *= (1 + shop_sapma)
  ```
- On other days:
  ```python
  price remains unchanged (copied from previous)
  ```
- Final pricing is stored in MongoDB as:
  ```json
  {
    "Product X Price": "45,000.00 TL",
    "Product X Shop Profit %": 9.5
  }
  ```
-![Main Menu](./csv_yedek/NormalCollusionShopGraph.jpeg)


### 🔄 Normal vs Collusion Comparison

| Property | Normal Shops | Collusion Shops |
|----------|---------------|------------------|
| Profit Source | Random variation | Fixed profit % + sapma |
| Price Updates | Individual, local | Coordinated, delayed |
| Manufacturer Selection | Random | 2 common + unique |
| Price Behavior | Uncorrelated | Synchronized pattern |

This synthetic process allows us to simulate real-world price manipulation scenarios with high fidelity.

---
## 📂 Output Artifacts

| File | Description |
|------|-------------|
| `shop_features2.csv` | Final dataset used for ML training |
| `collusion_groupsTest1.csv` | Labeled ground-truth shop clusters |
| `predicted_vs_actual_collusion_groups.csv` | Evaluation output |
| `collusion_model3.pkl` | Trained classifier |

---
## 🖼️ System UI Overview

### 🌍 Main Menu
The main dashboard offering entry points to all analytical and simulation modules.
![Main Menu](./csv_yedek/UI1.png)
### 📈 Product Simulation Panel
Create new products, define manufacturers and shops, and generate collusion shops for training purposes.
![Main Menu](./csv_yedek/UI2.png)
### 🤖 Machine Learning Collusion Detection
ML-based module with metrics like Accuracy, ARI, and NMI, along with classification reports and grouped shop predictions.
![Main Menu](./csv_yedek/UI6.png)
### 🤝 Rule-Based Collusion Detection
Detects collusion using actual profit timelines to extract leader-follower relationships and group synchronizations.
![Main Menu](./csv_yedek/UI3.png)
### 📊 Profit Visualization Module
Plot average daily prices per shop per product over a selected time interval to analyze coordinated pricing behaviors.
![Main Menu](./csv_yedek/UI4.png)
### ⚠️ Fraud Detection Dashboard
### Supports:
Machine Learning (Isolation Forest)
Rule-based anomaly scoring
Tables and summary reports identify fraudulent profit patterns.
![Main Menu](./csv_yedek/UI5.png)

---

## 🎯 Project Goals

- Full supply chain and market behavior simulation.
- Fraud and collusion detection models.
- Real-time detection systems foundation.

---

## 🔮 Future Improvements

- **Real-Time Market Monitoring Dashboard**
- **Anomaly Scoring Systems**
- **Deep Learning based Fraud Detection**
- **Cross-Manufacturer Supply Chain Analysis**

---

## 📌 Final Thoughts

This project builds a comprehensive, scalable system designed for academic, regulatory, and commercial uses.

> "Control the market by understanding it first."  — **Emre Analan**