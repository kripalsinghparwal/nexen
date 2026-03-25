import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import cv2
import os
from sklearn.model_selection import train_test_split
from datetime import datetime

CAPTCHA_LENGTH = 6
CHARACTERS = '0123456789'

def encode_label(text):
    return [CHARACTERS.index(c) for c in text]

def decode_label(label):
    return ''.join(CHARACTERS[c] for c in label)

def load_data(folder):
    X, y = [], []
    for filename in os.listdir(folder):
        if filename.endswith('.png'):
            label = filename.split('.')[0]
            img = cv2.imread(os.path.join(folder, filename), cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (200, 50)) / 255.0
            X.append(img.reshape(50, 200, 1))
            y.append(encode_label(label))
    return np.array(X), np.array(y)

# Load data
X, y = load_data(r'D:\\Nexensus_Projects\\GST_TaxPayer\\captcha_dataset\\')
y = tf.keras.utils.to_categorical(y, num_classes=len(CHARACTERS))
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.1)

# Define model
def build_model():
    inputs = layers.Input(shape=(50, 200, 1))
    x = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Flatten()(x)
    x = layers.Dense(1024, activation='relu')(x)

    outputs = [layers.Dense(len(CHARACTERS), activation='softmax')(x) for _ in range(CAPTCHA_LENGTH)]
    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer='adam',
        loss=['categorical_crossentropy'] * CAPTCHA_LENGTH,
        metrics=['accuracy'] * CAPTCHA_LENGTH
    )
    return model


model = build_model()
model.fit(X_train, [y_train[:, i] for i in range(CAPTCHA_LENGTH)],
          validation_data=(X_val, [y_val[:, i] for i in range(CAPTCHA_LENGTH)]),
          epochs=20, batch_size=32)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model.save(f'captcha_model_updated_{timestamp}.h5')
