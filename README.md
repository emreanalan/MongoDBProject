# MongoDB Manufacturer & Distributor Management System

> **Author:** Emre Analan  
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
├── Al_GD_Cop_fetching.py             
├── EUR_TRY_Fetching.py               
├── Others_Fetching.py                
├── asgari.py                         
├── electric.py                       
├── dogalgaz.py                       
├── Production.py                     
├── Manufacturer.py                   
├── Distributor.py                    
├── ProductsCollection.py             
├── Shops.py                          
├── Shop.py                           
├── Cheater.py                        
├── CheaterWithDateInterval.py        
├── CollusionDetection.py             
├── CollusionShop.py                  
├── NewCollusionShop.py               
├── FraudDetection.py                 
├── FraudDetectionWithProfit.py       
├── FeatureEngineering.py             
├── ModelTraining.py                  
├── ShopFeatureEngineering.py         
├── DataRetrieval.py                  
├── DataUpdater.py                    
├── DeleteData.py                     
├── Tests.py                          
├── Utils.py                          
├── MongoDbConnect.py                 
└── README.md                         
```

---

## 📝 How to Use

### 1. Fetching Raw Material Data
- `asgari.py`, `electric.py`, `dogalgaz.py`
- `Al_GD_Cop_fetching.py`, `EUR_TRY_Fetching.py`, `Others_Fetching.py`

**Note:** Weekend/holiday gaps are automatically filled.

### 2. Product Model Creation
- `Production.py`
- Use `insert_daily_costs()` to insert costs into the database.

### 3. Manufacturer & Distributor Databases
- `Manufacturer.py` and `Distributor.py`

### 4. Shops and Market Simulation
- `Shops.py`
- `Cheater.py`, `CheaterWithDateInterval.py`

### 5. Collusion & Fraud Detection
- `CollusionDetection.py`, `CollusionShop.py`, `NewCollusionShop.py`
- `FraudDetection.py`, `FraudDetectionWithProfit.py`

### 6. Feature Engineering & Model Training
- `FeatureEngineering.py`, `ShopFeatureEngineering.py`
- `ModelTraining.py`

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
