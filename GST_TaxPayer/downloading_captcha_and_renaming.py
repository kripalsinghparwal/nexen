############### Code to download capthas and store them after renaming with output #########
import requests
from bs4 import BeautifulSoup
import os
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import cv2
from sklearn.model_selection import train_test_split
from datetime import datetime

# Load the pre-trained model
model = load_model(r'D:\Nexensus_Projects\captcha_model_updated_20250530_121916.h5')

# Constants
CAPTCHA_LENGTH = 6
CHARACTERS = '0123456789'

# Create directory for downloads
os.makedirs('captcha_downloads', exist_ok=True)

# Example for a hypothetical captcha generator URL
base_url = "https://services.gst.gov.in/services/captcha?rnd=0.920321416851637"  # Replace with actual base URL

for i in range(1, 201):  # Download 50 images
    try:
        # Modify URL parameters if needed (some sites use session IDs)
        url = f"{base_url}id={i}"
        response = requests.get(url, stream=True, timeout=10)
        
        if response.status_code == 200:
            with open(f'captcha_downloads/captcha_{i}.png', 'wb') as f:
                f.write(response.content)
            print(f"Downloaded captcha_{i}.png")
        else:
            print(f"Failed to download image {i}")
    except Exception as e:
        print(f"Error downloading image {i}: {str(e)}")



# Block to load trained model 
# from tensorflow.keras.models import load_model
# model = load_model('captcha_model.h5') 

def predict_captcha(model, image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (200, 50)) / 255.0
    img = img.reshape(1, 50, 200, 1)
    preds = model.predict(img)
    # print(preds)
    pred_text = ''.join(CHARACTERS[np.argmax(p)] for p in preds)
    return pred_text

# print(predict_captcha(model, r'C:\Users\PC\Pictures\Saved Pictures\captcha.png'))
# print(predict_captcha(model, r'D:\Nexensus_Projects\red_line_removed_captcha.png'))
# for i in range(1, 31):
#     print(r'C:\Users\PC\Pictures\Saved Pictures\captcha ({}).png'.format(i))
#     print(i,"  ", predict_captcha(model, r'C:\Users\PC\Pictures\Saved Pictures\captcha_{}.png'.format(i)))

import os
# Adjust your folder path accordingly
folder = r'D:\Nexensus_Projects\GST_TaxPayer\captcha_downloads'

for i in range(1, 201):
    # Original filename
    original_filename = os.path.join(folder, f'captcha_{i}.png')

    # Get predicted label
    predicted_label = predict_captcha(model, original_filename)  # e.g., "232424"
    
    # New filename based on prediction
    new_filename = os.path.join(folder, f'{predicted_label}.png')

    # Rename the file
    if os.path.exists(original_filename):
        os.rename(original_filename, new_filename)
        print(f'Renamed: {original_filename} → {new_filename}')
    else:
        print(f'❌ File not found: {original_filename}')
