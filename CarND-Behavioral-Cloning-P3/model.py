import os
import csv
import cv2
import numpy as np
import sklearn
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Flatten, Dense, Lambda, Cropping2D, Dropout
from keras.layers.convolutional import Convolution2D
from keras.layers.pooling import MaxPooling2D

csv_file = './DATA/driving_log.csv'

if __name__ == '__main__':
    samples = []
    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile)
        for line in reader:
            samples.append(line)

    train_samples, validation_samples = train_test_split(samples, test_size=0.2)

    def generator(samples, batch_size=32, train=False):
        angle_correction = [0., +.2, -.2]
        num_samples = len(samples)
        while 1: # Loop forever so the generator never terminates
            samples = sklearn.utils.shuffle(samples)
            for offset in range(0, num_samples, batch_size):
                batch_samples = samples[offset:offset+batch_size]

                images = []
                angles = []
                for batch_sample in batch_samples:
                    for i in range(3):
                        name = './DATA/IMG/'+batch_sample[i].split('/')[-1]
                        image = cv2.imread(name)
                        angle = float(batch_sample[3]) + angle_correction[i]
                        images.append(image)
                        angles.append(angle)

                    augmented_images, augmented_angles = [], []
                    for image, angle in zip(images,angles):
                        augmented_images.append(image)
                        augmented_angles.append(angle)
                        augmented_images.append(cv2.flip(image,1))
                        augmented_angles.append(angle*-1.0)

                def sampleLists(X,y, sample=0.5):
                    X_shuff, y_shuff = sklearn.utils.shuffle(X,y)
                    size = int(len(X)*sample)
                    return np.array(X_shuff[:size]), np.array(y_shuff[:size])

                sample = 0.5 if train else 1.0
                yield sampleLists(augmented_images, augmented_angles, sample=sample)

    batch_size = 32
    # compile and train the model using the generator function
    train_generator = generator(train_samples, batch_size=batch_size, train=True)
    validation_generator = generator(validation_samples, batch_size=batch_size)

    model = Sequential()
    model.add(Lambda(lambda x: x / 255.0 - 0.5, input_shape=(160,320,3)))
    model.add(Cropping2D(cropping=((70,25),(0,0))))
    model.add(MaxPooling2D())
    model.add(Convolution2D(6,5,5,subsample=(2,2),activation="relu"))
    model.add(MaxPooling2D())
    model.add(Convolution2D(6,5,5,activation="relu"))
    model.add(MaxPooling2D())
    model.add(Flatten())
    model.add(Dense(120))
    model.add(Dropout(0.5))
    model.add(Dense(84))
    model.add(Dense(1))

    model.compile(loss='mse', optimizer='nadam')
    model.fit_generator(train_generator, samples_per_epoch=len(train_samples)*3,
                        validation_data=validation_generator, nb_val_samples=len(validation_samples)*6,
                        nb_epoch=4)
    
    #save model
    model.save('./model.h5')