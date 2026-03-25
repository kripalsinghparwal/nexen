##### Code to train model already trained with additional/new dataset #############

from tensorflow.keras.optimizers import Adam
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
from sklearn.model_selection import train_test_split
from datetime import datetime

# Load the pre-trained model :-  load latest saved mode
model = load_model('captcha_model_updated_20250604_104518.h5')

# Constants
CAPTCHA_LENGTH = 6
CHARACTERS = '0123456789'

# Use a smaller learning rate (e.g., 0.0001 instead of the default 0.001)
model.compile(
    optimizer=Adam(learning_rate=1e-4),
    loss=['categorical_crossentropy'] * CAPTCHA_LENGTH,
    metrics=['accuracy'] * CAPTCHA_LENGTH
)

# Label encoding/decoding
def encode_label(text):
    return [CHARACTERS.index(c) for c in text]

def load_data(folder):
    X, y = [], []
    for filename in os.listdir(folder):
        if filename.endswith('.png'):
            label = filename.split('.')[0]
            if len(label) != CAPTCHA_LENGTH:
                continue
            img = cv2.imread(os.path.join(folder, filename), cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (200, 50)) / 255.0
            X.append(img.reshape(50, 200, 1))
            y.append(encode_label(label))
    return np.array(X), np.array(y)

# Load new data
X_new, y_new = load_data('resolved_captchaset/')  # Replace with your new dataset folder
y_new = tf.keras.utils.to_categorical(y_new, num_classes=len(CHARACTERS))
X_train, X_val, y_train, y_val = train_test_split(X_new, y_new, test_size=0.1)



# Continue training the model
model.fit(
    X_train, [y_train[:, i] for i in range(CAPTCHA_LENGTH)],
    validation_data=(X_val, [y_val[:, i] for i in range(CAPTCHA_LENGTH)]),
    epochs=10,  # You can adjust the number of additional epochs
    batch_size=32
)

# Save the updated model
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model.save(f'captcha_model_updated_{timestamp}.h5')
