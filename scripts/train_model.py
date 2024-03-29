import numpy as np
import matplotlib.pyplot as plt
import os
import cv2
import random
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras import layers, models
from tensorflow.keras.layers import Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping

DATADIR = "assets/dataset"
CATEGORIES = ["bb", "bk", "bn", "bp", "bq", "br", "wb", "wk", "wn", "wp", "wq", "wr", "zEmpty"]

X = []
Y = []

def create_training_data():
    for category in CATEGORIES:
        path = os.path.join(DATADIR, category)
        class_num = CATEGORIES.index(category)
        for img in os.listdir(path):
            img_path = os.path.join(path, img)
            img_array = cv2.imread(img_path, cv2.IMREAD_ANYCOLOR)
            if img_array is not None:
                IMG_SIZE = 100
                resized_array = cv2.resize(img_array, (IMG_SIZE, IMG_SIZE))
                if img_array is not None and len(img_array.shape) == 3 and img_array.shape[2] != 3:
                    resized_array = cv2.cvtColor(resized_array, cv2.COLOR_GRAY2BGR)
                X.append(resized_array)
                Y.append(class_num)
            else:
                print(f"Error reading image: {img_path}")

create_training_data()
X = np.stack(X)
Y = np.array(Y)

XY = list(zip(X, Y))
random.shuffle(XY)
X, Y = zip(*XY)

IMG_SIZE = 100
X = np.array(X).reshape(-1, IMG_SIZE, IMG_SIZE, 3)
X = X.astype('float32') / 255.0
Y = to_categorical(Y)

X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=70)

def create_model_with_dropout():
    model = models.Sequential()
    model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(100, 100, 3)))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.MaxPooling2D((2, 2)))
    model.add(layers.Conv2D(64, (3, 3), activation='relu'))
    model.add(layers.Flatten())
    model.add(layers.Dense(64, activation='relu'))
    model.add(Dropout(0.3))
    model.add(layers.Dense(len(CATEGORIES), activation='softmax'))
    return model

model_with_dropout = create_model_with_dropout()

model_with_dropout.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# Data augmentation
datagen = ImageDataGenerator(
    rotation_range=10,
    width_shift_range=0.1,
    height_shift_range=0.1,
    horizontal_flip=False)

datagen.fit(X_train)

# Add the EarlyStopping callback
early_stopping = EarlyStopping(monitor='val_loss', patience=8, mode='min')

history_with_dropout = model_with_dropout.fit(datagen.flow(X_train, Y_train, batch_size=32),
                    steps_per_epoch=len(X_train) / 32, epochs=64,
                    validation_data=(X_test, Y_test),
                    callbacks=[early_stopping])


test_loss_dropout, test_acc_dropout = model_with_dropout.evaluate(X_test, Y_test, verbose=2)
print('\nTest accuracy with dropout and data augmentation:', test_acc_dropout)
model_with_dropout.save(f"models/model_{test_acc_dropout}.h5")
