##########  Code to capture the code from captcha with same image and cleaned image using google lens#################

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import pyautogui
import pyperclip
import re

# Step 1: Read the image
captcha_url = r"C:\Users\PC\Pictures\Saved Pictures\captcha2.png"
cleaned_captcha_url = r"D:\Nexensus_Projects\captcha_cleaned.png"

captcha_data = {
    "uncleaned" : [captcha_url, None],
    "cleaned" : [cleaned_captcha_url, None]
}
image = cv2.imread(captcha_url)

# Step 2: Convert image to HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Step 3: Define red color range and create a mask
# Red has two hue ranges in HSV
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([160, 100, 100])
upper_red2 = np.array([180, 255, 255])

mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = cv2.bitwise_or(mask1, mask2)

# Optional: dilate mask to cover thicker lines
kernel = np.ones((3, 3), np.uint8)
mask = cv2.dilate(mask, kernel, iterations=1)

# Step 4: Inpaint the image to remove the red line
inpainted = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

# Step 5: Save or show the result
cv2.imwrite("captcha_cleaned.png", inpainted)
# cv2.imshow("Cleaned CAPTCHA", inpainted)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

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


copied_text = pyperclip.copy("")
# while copied_text !=6:

for i in captcha_data:
    url = captcha_data[i][0]
    print("current captcha url :", url)
    for j in range(10):
        # Set up the browser (make sure you have the correct driver installed)
        driver = webdriver.Chrome()
        # driver.get(r"D:\Nexensus_Projects\captcha_cleaned.png")
        # driver.get(captcha_url)
        # driver.get(cleaned_captcha_url)
        driver.get(url)
        time.sleep(1)
        if j%2 == 0:
            driver.maximize_window()

        # Open the webpage
        # driver.get("https://services.gst.gov.in/services/captcha")

        # Wait for the page to load
        driver.implicitly_wait(3)
        

        # Locate the image or any other element
        element = driver.find_element(By.TAG_NAME, "img")  # Use appropriate locator

        # Create action chain and perform right-click
        actions = ActionChains(driver)
        actions.context_click(element).perform()

        # Pause to visually inspect (optional)
        time.sleep(3)

        try:
            # Click on 'Search with Google Lens'
            click_button(r'C:\Users\PC\Pictures\Screenshots\seach_with_google_lens.png')

            # Wait for Lens to load
            time.sleep(4)

            # click ok on pop up 
            click_button(r'C:\Users\PC\Pictures\Screenshots\pop_up_ok.png')
            time.sleep(2)

            # Click 'Select Text'
            click_button(r'C:\Users\PC\Pictures\Screenshots\select_text.png')
            time.sleep(2)

            # Optionally click 'Copy Text'
            click_button(r'C:\Users\PC\Pictures\Screenshots\copy3.png')
            time.sleep(2)
        except Exception as e:
            print(e)


        driver.quit()

        # Get the text from clipboard
        copied_text = pyperclip.paste()
        print("Extracted Copied text:", copied_text)
        copied_text = re.sub(r'\D', '', copied_text)
        print("Cleaned Copied text:", copied_text)
        if len(copied_text) == 6 and copied_text.isdigit():
            captcha_data[i][1] = copied_text
            break

print(captcha_data)


