import time
import pymongo
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime  # Import datetime module

# MongoDB connection setup with your provided connection string
mongo_connection_string = "mongodb+srv://emreanlan550:emreanlan@cluster0.od7u9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(mongo_connection_string)

# Connect to the Final_Project database and Asgari_Ucret collection
db = client["Final_Project"]
collection = db["Asgari/Ucret"]

# Set up Selenium WebDriver with the Service object
driver_path = 'C:/Users/emrea/Desktop/Selenium/Driver-v1/chromedriver.exe'
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# Function to scrape Asgari Ücret data
def scrape_asgari_ucret():
    # Open the specified website
    driver.get("https://www.csgb.gov.tr/asgari-ucret/")

    time.sleep(3)  # Let the page load

    asgari_ucret_data = []

    try:
        title_element = driver.find_element(By.XPATH, "//*[@id=\"printArea\"]/content/table[1]/tbody/tr/td/table/tbody/tr[5]/td[1]/p/strong")
        description_element = driver.find_element(By.XPATH, "//*[@id=\"printArea\"]/content/table[1]/tbody/tr/td/table/tbody/tr[5]/td[2]/p")
        time_period_element = driver.find_element(By.XPATH, "//*[@id=\"printArea\"]/content/p[4]/strong[1]")

        title = title_element.text
        description = description_element.text
        time_period = time_period_element.text

        # Append data to the list with the current date
        asgari_ucret_data.append({
            "title": title,
            "Asgari Ücret": description,
            "Time Period": time_period  # Store the time period
        })
    except Exception as e:
        print(f"Error extracting data: {e}")

    # Insert data into MongoDB
    if asgari_ucret_data:
        collection.insert_many(asgari_ucret_data)
        print(f"Inserted {len(asgari_ucret_data)} documents into the 'Asgari_Ucret' collection.")

    # Close the browser
    driver.quit()

# Function to scrape Doğal Gaz Ücreti data
def scrape_dogal_gaz_ucreti():
    # Open the specified website
    driver.get("https://dogalgaz-fatura.hesaplama.in/dogalgaz-fatura-hesaplama")

    time.sleep(3)  # Let the page load

    # Select the option "ankara_baskentgaz"
    select_element = driver.find_element(By.XPATH, "//*[@id='singleContent']/form/table/tbody/tr[1]/td/select")
    option = select_element.find_element(By.XPATH, "//*[@id='singleContent']/form/table/tbody/tr[1]/td/select/option[6]")
    option.click()

    # Type 100 in the text box
    text_box = driver.find_element(By.XPATH, "//*[@id='singleContent']/form/table/tbody/tr[2]/td/input")
    text_box.send_keys("100")

    # Click the calculate button
    calculate_button = driver.find_element(By.XPATH, "//*[@id='singleContent']/form/table/tbody/tr[3]/td[2]/input")
    calculate_button.click()

    time.sleep(3)  # Let the new page load

    dogal_gaz_data = []

    try:
        title_element = driver.find_element(By.XPATH, "//*[@id='singleContent']/b[1]")
        dogalgaz_ucreti_element = driver.find_element(By.XPATH, "//*[@id='singleContent']/b[2]")
        approved_date = "1 August 2024"

        title = title_element.text
        dogalgaz_ucreti = dogalgaz_ucreti_element.text

        # Append data to the list with the current date
        dogal_gaz_data.append({
            "title": "100m^3 için Doğalgaz Ücreti",
            "Doğalgaz Ücreti": dogalgaz_ucreti,
            "Approved Date": approved_date  # Use the provided date
        })
    except Exception as e:
        print(f"Error extracting data: {e}")

    # Insert data into MongoDB
    if dogal_gaz_data:
        collection.insert_many(dogal_gaz_data)
        print(f"Inserted {len(dogal_gaz_data)} documents into the 'DogalGaz_Ucreti' collection.")

    # Close the browser
    driver.quit()

# Function to scrape Electrik Ücreti data
def scrape_electrik_ucreti():
    # Open the specified website
    driver.get("https://enerjiajansi.com.tr/elektrik-birim-fiyatlari/")

    time.sleep(3)  # Let the page load

    electik_ucreti_data = []

    try:
        title_element = driver.find_element(By.XPATH, "//*[@id='the-post']/div[2]/figure[1]/div/table/tbody/tr[1]/td[6]/strong")
        electrik_ucreti_element = driver.find_element(By.XPATH, "//*[@id='the-post']/div[2]/figure[1]/div/table/tbody/tr[2]/td[6]")
        approved_date = "1 July 2024"

        title = title_element.text
        electrik_ucreti = electrik_ucreti_element.text + " TL"

        # Append data to the list with the current date
        electik_ucreti_data.append({
            "title": title,
            "Electrik Ücreti": electrik_ucreti,
            "Approved Date": approved_date  # Use the provided date
        })
    except Exception as e:
        print(f"Error extracting data: {e}")

    # Insert data into MongoDB
    if electik_ucreti_data:
        collection.insert_many(electik_ucreti_data)
        print(f"Inserted {len(electik_ucreti_data)} documents into the 'Electrik_Ücreti' collection.")

    # Close the browser
    driver.quit()

# Run the function to scrape and store data
scrape_asgari_ucret()
scrape_dogal_gaz_ucreti()
scrape_electrik_ucreti()
