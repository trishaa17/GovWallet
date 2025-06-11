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

DOWNLOAD_DIR = r"C:\Users\User\OneDrive - WORLD AQUATICS CHAMPIONSHIPS SINGAPORE PTE. LTD\GovWallet"
EXISTING_FILENAME = "govwallet_data.csv"

def main():
    download_csv(DOWNLOAD_DIR)

def download_csv(download_dir):
    # Setup download folder
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(options=chrome_options)

    # Login credentials and URL
    deegixpage = "https://ws-wallet-wch-stg.nexframework.com/admin/login?reason=SIGN_OUT"
    finmanager = "fin-manager1@nexframework.com"
    finmanagerPass = "NFpass@1"

    driver.get(deegixpage)
    wait = WebDriverWait(driver, 30)

    # Login process
    email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    email_input.send_keys(finmanager)
    pass_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
    pass_input.send_keys(finmanagerPass)

    def fields_are_filled(driver):
        email = driver.find_element(By.CSS_SELECTOR, "input[type='email']").get_attribute("value")
        password = driver.find_element(By.CSS_SELECTOR, "input[type='password']").get_attribute("value")
        return email.strip() != "" and password.strip() != ""

    wait.until(fields_are_filled)
    login_button = driver.find_element(By.CLASS_NAME, "button")
    login_button.click()

    # Click Import/Export
    togglebtns = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "toggle")))
    impexp = togglebtns[3]  # index 3 for import/export
    wait.until(EC.element_to_be_clickable(impexp))
    impexp.click()

    expbtn = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "a.button[href='/admin/content']"
    )))
    expbtn.click()

    target_link = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "a[href='/admin/content/allowance_history?bookmark=102']"
    )))
    target_link.click()

    export_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[.//span[text()='Export Items']]"
    )))
    export_btn.click()


    # Change limit to unlimited
    limit = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']")))
    limit.send_keys("\b\b")

    toggle_buttons = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "toggle")))

    # for i, btn in enumerate(toggle_buttons):
    #     print(f"Index {i}: '{btn.text.strip()}'")

    addFieldbtn = toggle_buttons[5]  
    wait.until(EC.element_to_be_clickable(addFieldbtn))
    addFieldbtn.click()

    select_all_li = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//li[text()='Select All']")
    ))
    select_all_li.click()


    # Download CSV
    download_icon_button = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[.//i[@data-icon='download']]"
    )))
    download_icon_button.click()
    print("Started downloading allowance CSV...")

    time.sleep(5)  # Let the download start
    driver.quit()

    update_existing_file_with_new_data(download_dir, EXISTING_FILENAME)

def update_existing_file_with_new_data(download_dir, existing_filename):
    timeout = 30
    start_time = time.time()
    downloaded_file = None

    while time.time() - start_time < timeout:
        for f in os.listdir(download_dir):
            if "allowance" in f.lower() and f.lower().endswith(".csv") and not f.endswith(".crdownload"):
                downloaded_file = f
                break
        if downloaded_file:
            break
        time.sleep(1)

    if not downloaded_file:
        raise FileNotFoundError("New allowance CSV did not download in time.")

    new_path = os.path.join(download_dir, downloaded_file)
    existing_path = os.path.join(download_dir, existing_filename)

    # Load and overwrite the existing file's contents
    new_df = pd.read_csv(new_path)
    new_df.to_csv(existing_path, index=False)
    print(f"Updated contents of '{existing_path}' while preserving share link.")

    # Clean up
    if new_path != existing_path:
        os.remove(new_path)

if __name__ == '__main__':
    main()
