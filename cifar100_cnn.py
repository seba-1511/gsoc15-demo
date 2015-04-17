import numpy as np
from keras.datasets import cifar100
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD
from keras.utils import np_utils, generic_utils

'''
    Train a (fairly simple) deep CNN on the CIFAR10 small images dataset.

    GPU run command:
        THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python cifar10_cnn.py

    It gets down to 0.65 test logloss in 25 epochs, and down to 0.55 after 50 epochs.
    (it's still underfitting at that point, though).
'''

batch_size = 128
nb_classes = 10
nb_epoch = 5
data_augmentation = True
all_time_best = []


for ds_idx in xrange(10):
    # the data, shuffled and split between tran and test sets
    (X_train, y_train), (X_test, y_test) = cifar100.load_data(test_split=0.15)

    train_idx = np.where((y_train >= ds_idx * 10) & (y_train < (1 + ds_idx) * 10))[0]
    test_idx = np.where((y_test >= ds_idx * 10) & (y_test < (1 + ds_idx) * 10))[0]

    X_train = np.array([X_train[i] for i in train_idx])
    y_train  = np.array([y_train[i] for i in train_idx])
    X_test = np.array([X_test[i] for i in test_idx])
    y_test = np.array([y_test[i] for i in test_idx])

    print X_train.shape[0], 'train samples'
    print X_test.shape[0], 'test samples'

    y_train -= 90
    y_test -= 90

    # convert class vectors to binary class matrices
    Y_train = np_utils.to_categorical(y_train, nb_classes)
    Y_test = np_utils.to_categorical(y_test, nb_classes)

    model = Sequential()

    model.add(Convolution2D(32, 3, 3, 3, border_mode='full'))
    model.add(Activation('relu'))
    model.add(Dropout(0.8))
    model.add(Convolution2D(32, 32, 3, 3))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(poolsize=(2, 2)))
    model.add(Dropout(0.75))

    model.add(Convolution2D(64, 32, 3, 3, border_mode='full'))
    model.add(Activation('relu'))
    model.add(Dropout(0.7))
    model.add(Convolution2D(64, 64, 3, 3))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(poolsize=(2, 2)))
    model.add(Dropout(0.6))

    model.add(Flatten(64*8*8))
    model.add(Dense(64*8*8, 512, init='normal'))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))

    model.add(Dense(512, nb_classes, init='normal'))
    model.add(Activation('softmax'))

    # let's train the model using SGD + momentum (how original).
    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy', optimizer=sgd)

    if not data_augmentation:
        print "Not using data augmentation or normalization"

        X_train = X_train.astype("float32")
        X_test = X_test.astype("float32")
        X_train /= 255
        X_test /= 255
        model.fit(X_train, Y_train, batch_size=batch_size, nb_epoch=10)
        score = model.evaluate(X_test, Y_test, batch_size=batch_size)
        print 'Test score:', score

    else:
        print "Using real time data augmentation"

        # this will do preprocessing and realtime data augmentation
        datagen = ImageDataGenerator(
            featurewise_center=True, # set input mean to 0 over the dataset
            samplewise_center=False, # set each sample mean to 0
            featurewise_std_normalization=True, # divide inputs by std of the dataset
            samplewise_std_normalization=False, # divide each input by its std
            zca_whitening=False, # apply ZCA whitening
            rotation_range=20, # randomly rotate images in the range (degrees, 0 to 180)
            width_shift_range=0.3, # randomly shift images horizontally (fraction of total width)
            height_shift_range=0.3, # randomly shift images vertically (fraction of total height)
            horizontal_flip=True, # randomly flip images
            vertical_flip=False) # randomly flip images

        # compute quantities required for featurewise normalization
        # (std, mean, and principal components if ZCA whitening is applied)
        datagen.fit(X_train)
        best_score = 0.0
        best_epoch = 0

        for e in range(nb_epoch):
            print '-'*40
            print 'Epoch', e
            print '-'*40
            print "Training..."
            # batch train with realtime data augmentation
            progbar = generic_utils.Progbar(X_train.shape[0])
            for X_batch, Y_batch in datagen.flow(X_train, Y_train):
                loss = model.train(X_batch, Y_batch)
                progbar.add(X_batch.shape[0], values=[("train loss", loss)])

            print "Testing..."
            # test time!
            progbar = generic_utils.Progbar(X_test.shape[0])
            pred = model.predict_classes(X_test, batch_size=batch_size)
            score = np_utils.accuracy(pred, Y_test)
            best_epoch, best_score = (best_epoch, best_score) if best_score >= score else (e, score)
            print 'Score: ', score
            print 'Best: ', best_score, ' at epoch: ', best_epoch
            #for X_batch, Y_batch in datagen.flow(X_test, Y_test):
                #score = model.test(X_batch, Y_batch)
                #progbar.add(X_batch.shape[0], values=[("test loss", score)])
        all_time_best.append((best_epoch, best_score))


for epoch, score in all_time_best:
    print 'At: ', epoch, ', best score: ', score








