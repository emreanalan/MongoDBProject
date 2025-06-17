# 🧠 Collusion Group Detection System (CGDS)

## 📜 Introduction

Collusion among online vendors poses a significant challenge in maintaining fair marketplaces. This project is designed to **detect collusive groups of shops** based on simulated behavior, profit margins, and pricing similarities. Leveraging **synthetic data generation**, **feature engineering**, and **supervised machine learning**, the system identifies suspicious shop clusters that may exhibit coordinated manipulation tactics.

The system operates end-to-end, from data fetching and shop simulation to feature extraction and model training. The dataset is stored in **MongoDB Atlas**, processed using **Python**, and analyzed through **scikit-learn** models.

---

## 🎯 Project Objectives

* **Simulate realistic shop behavior** using manufacturer/product dynamics.
* **Generate both normal and collusive shops** with overlapping patterns.
* **Engineer behavioral features** that represent profit variability, price consistency, manufacturer dependencies, etc.
* **Train machine learning models** to classify collusive shops and group them by similarity.
* **Evaluate model predictions** against ground truth clusters.

---

## 🛠️ System Architecture

### Main Components

| Stage | Script                          | Description                                                                                          |
| ----- | ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1     | `Al_GD_Cop_fetching.py`         | Fetch commodity prices (Gold, Copper, etc.) from Yahoo Finance and store in MongoDB.                 |
| 2     | `EUR_TRY_Fetching.py`           | Fetch currency exchange rates (EUR/TRY, USD/TRY) and store in MongoDB.                               |
| 3     | `RandomShopGenerator.py`        | Create simulated shops, either normal or collusion-based, based on cached manufacturer/product data. |
| 4     | `labeling.py`                   | Process test sets and produce ground-truth collusion groups.                                         |
| 5     | `feature_engineering.py`        | Extract detailed shop-level features and pairwise similarities.                                      |
| 6     | `model_training.py`             | Train classification model using extracted features.                                                 |
| 7     | `CollusionTraining.py`          | Apply model to new test data and evaluate performance.                                               |
| 8     | `generate_similarity_matrix.py` | (Optional) Compute detailed pairwise shop similarity metrics.                                        |

---

## 🔄 End-to-End Pipeline

### Step-by-step execution:

```bash
# Step 1: Fetch commodity & currency data
python Al_GD_Cop_fetching.py
python EUR_TRY_Fetching.py

# Step 2: Simulate shops
python RandomShopGenerator.py

# Step 3: Label collusion groups
python labeling.py

# Step 4: Extract features
python feature_engineering.py

# Step 5: Train model
python model_training.py

# Step 6: Evaluate model on new data
python CollusionTraining.py
```

---

## 📊 Feature Engineering

The `feature_engineering.py` script generates two major outputs:

* `shop_features2.csv`: A file containing feature vectors per shop
* `shop_similarity_matrixTest1.csv`: Pairwise similarity metrics

### Extracted Features:

* `price_change_count`
* `product_price_diff`
* `product_price_variance`
* `price_change_frequency`
* `profit_percentage_variability`
* `product_price_consistency`
* `manufacturer_count`
* `avg_profit_pct`, `profit_pct_std`
* `is_collusion`, `collusion_group`

### Key Functions:

```python
def extract_product_price_history(shop_path):
    """Extracts profit history of products from a shop JSON."""
    # Reads product pricing behavior per shop per day
    ...


def compute_product_price_diff(product_history):
    """Computes standard deviation of product profits."""
    ...


def compute_product_price_consistency(shop_id, product_history, all_shop_profits):
    """Measures profit price similarity of a shop compared to others."""
    ...


def extract_features(args):
    """Combines all metrics into a final feature vector."""
    ...
```

---

## 🤖 Model Training

Implemented in `model_training.py` using `RandomForestClassifier`.

```python
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

### Evaluation Functions:

```python
from sklearn.metrics import classification_report, accuracy_score
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))
```

Visualizations:

```python
import seaborn as sns
sns.heatmap(confusion_matrix(y_test, y_pred), annot=True)
```

---

## 📈 Model Evaluation

`CollusionTraining.py` loads the trained model and applies it to new data.

```python
model = joblib.load('collusion_model3.pkl')
y_pred = model.predict(X_new_test)
print(classification_report(y_true, y_pred))
```

### Additional Cluster Metrics:

```python
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
print("ARI:", adjusted_rand_score(y_true, y_pred))
print("NMI:", normalized_mutual_info_score(y_true, y_pred))
```

---

## 📂 Output Artifacts

| File                                       | Description                        |
| ------------------------------------------ | ---------------------------------- |
| `shop_features2.csv`                       | Final dataset used for ML training |
| `collusion_groupsTest1.csv`                | Labeled ground-truth shop clusters |
| `predicted_vs_actual_collusion_groups.csv` | Evaluation output                  |
| `collusion_model3.pkl`                     | Trained classifier                 |

---

## 📌 Requirements

```txt
yfinance
pymongo
pandas
numpy
scikit-learn
matplotlib
seaborn
tqdm
joblib
```

Install via:

```bash
pip install -r requirements.txt
```

---

## 📬 Author

**Emre Analan**
GitHub: [@emreanalan](https://github.com/emreanalan)

---

## 📜 License

MIT License. Feel free to use, distribute, and modify with attribution.
