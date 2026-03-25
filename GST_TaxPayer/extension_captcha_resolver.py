##################### Code to resolve captcha using chrome extension ################################

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

captcha_image_url = r"C:\Users\PC\Pictures\Saved Pictures\captcha3.png"
options = Options()
# options.add_extension(r"C:\Users\PC\Downloads\test.crx")

driver = webdriver.Chrome(options=options)

driver.get("https://chromewebstore.google.com/detail/nopecha-captcha-solver/dknlfmjaanfblgfdfebhijalfmhmjjjo?utm_source=ext_app_menu")
time.sleep(5)

buttons = driver.find_elements(By.TAG_NAME, 'button')
for button in buttons:
    if button.text.strip() == "Add to Chrome":
        button.click()
        time.sleep(2)

def click_button(image_name, confidence=0.9, timeout=10):
    """Tries to locate and click a button by its image."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        location = pyautogui.locateCenterOnScreen(image_name, confidence=confidence)
        if location:
            pyautogui.click(location)
            return True
        time.sleep(0.5)
    print(f"Could not find: {image_name}")
    return False

# click ok on pop up 
click_button(r'C:\Users\PC\Pictures\Screenshots\add_extension.png')
time.sleep(2)

driver.get("https://azcaptcha.com/demo")
time.sleep(1)
try:
    driver.find_element(By.CLASS_NAME, "cc-btn.cc-dismiss").click()
    print("got it popup clicked")
except:
    pass
time.sleep(15)



driver.find_element(By.CLASS_NAME, "col-sm-8.fileinput").find_element(By.TAG_NAME, 'input').send_keys(captcha_image_url)
time.sleep(2)

try:
    driver.find_element(By.CLASS_NAME, "cc-btn.cc-dismiss").click()
    time.sleep(1)
    print("got it popup clicked")
except:
    pass

try:
    driver.find_element(By.ID, 'demo_image_upload').click()
    time.sleep(5)
except:
    pass


retry_delay = 2  # seconds

while True:
    try:
        captcha_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert.alert-success'))
        )
        captcha = captcha_element.text
        print("captcha:", captcha)
        break  # Exit loop on success
    except Exception as e:
        print(f"Retrying... Error: {e}")
        time.sleep(retry_delay)


# captcha = driver.find_element(By.CLASS_NAME, 'alert.alert-success').text
# print("captcha :", captcha)
