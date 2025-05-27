from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import time
import pandas as pd


DOWNLOAD_DIR = r"C:\Users\User\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD\WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD - Technology & Innovation\Ewallet"
REJECTED = 2
COLLECTED = 1
PRINTED = 0

def main():
    download_csv(DOWNLOAD_DIR)

def download_csv(download_dir):
    #set up download foler
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory" : download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(options=chrome_options)
    new_name = "govwallet_data.csv"

    def find_csv_file():
        for f in os.listdir(download_dir):
            if "allowance" in f.lower() and f.lower().endswith(".csv"):
                return f
        return

    def delete_old_csv():
        file_found = find_csv_file()
        if file_found:
            path = os.path.join(download_dir, file_found)
            os.remove(path)
        
        return

    def rename_file():
        timeout = 30  # seconds
        start_time = time.time()
        downloaded_file = None

        # Wait until a file containing 'govwallet_data' appears and is fully downloaded
        while time.time() - start_time < timeout:
            for f in os.listdir(download_dir):
                if "allowance" in f.lower() and f.lower().endswith(".csv"):
                    if not f.endswith(".crdownload"):  # Chrome temp download extension
                        downloaded_file = f
                        break
            if downloaded_file:
                break
            time.sleep(1)

        if not downloaded_file:
            raise FileNotFoundError("govwallet_data.csv did not download in time.")

        # Rename file
        old_path = os.path.join(download_dir, downloaded_file)
        new_path = os.path.join(download_dir, new_name)
        if os.path.exists(new_path):
            os.remove(new_path)  # Remove if already exists to avoid rename error
        os.rename(old_path, new_path)
        print(f"Renamed '{downloaded_file}' to '{new_name}'")


    #delete old govwallet_data.csv
    delete_old_csv()

    #deegix info
    deegixpage = "https://ws-wallet-wch-stg.nexframework.com/admin/login?reason=SIGN_OUT"
    finmanager = "fin-manager1@nexframework.com"
    finmanagerPass = "NFpass@1"

    #Open login page
    driver.get(deegixpage)

    #input email, waits up to 30s for page to load otherwise TimeoutException
    wait = WebDriverWait(driver, 30)
    email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    email_input.send_keys(finmanager)

    #input password
    pass_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
    pass_input.send_keys(finmanagerPass)

    #click login
    def fields_are_filled(driver): #checks if email and pass are filled
        email = driver.find_element(By.CSS_SELECTOR, "input[type='email']").get_attribute("value")
        password = driver.find_element(By.CSS_SELECTOR, "input[type='password']").get_attribute("value")
        return email.strip() != "" and password.strip() != ""

    wait.until(fields_are_filled)
    login_button = driver.find_element(By.CLASS_NAME, "button")
    login_button.click()

    

    #click import/export
    #find all buttons with class "toggle"
    togglebtns = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "toggle")))
    impexp = togglebtns[3] #import/export toggle button is at index 3
    wait.until(EC.element_to_be_clickable(impexp))
    impexp.click()

    #get all with class "button"
    btns = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "button")))
    expbtn = btns[13] #export button at index 13
    wait.until(EC.element_to_be_clickable(expbtn))
    expbtn.click()

    #change limit to unlimited
    limit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']")))
    limit.send_keys("\b\b")

    #download
    # Wait for and click the button that contains the <i> with data-icon="download"
    download_icon_button = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[.//i[@data-icon='download']]"
    )))
    download_icon_button.click()
    print("Downloaded govwallet_data.csv")


    time.sleep(5)
    driver.quit()


    #rename file
    rename_file()

    return


if __name__ == '__main__':
    main()