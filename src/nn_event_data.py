# -*- coding: utf-8 -*-
"""
This file contains the run code for a simple feedforward neural network to 
classify different event types.
"""

# Code from other files in the repo
import models.sequential_models as sequential_models
import utilities.plotlib as plotlib

# Python libraries
import numpy as np
import time
from sklearn.model_selection import train_test_split

ROOT = "C:\\{Directory containing data}\\ml_postproc\\"
data_to_collect = ['ttH125_part1-1', 
                   'TTTo2L2Nu', 
                   'TTToHadronic', 
                   'TTToSemiLeptonic']

# -------------------------------- Data setup --------------------------------

event_data = np.load('preprocessed_event_data')
event_labels = np.load('preprocessed_event_labels')
sample_weight = np.load('preprocessed_sample_weights')

test_fraction = 0.2
data_train, data_test, labels_train, labels_test, sw_train, sw_test  = \
    train_test_split(event_data.data, event_labels, 
                     sample_weight, test_size=test_fraction)

# ------------------------------ Model training -------------------------------

model = sequential_models.base(42, 4)

print("Fit sequential model on training data...")
START = time.time()
history = model.fit(data_train, labels_train, 
                    validation_data=(data_test, labels_test), 
                    sample_weight=sw_train, epochs=16, verbose=2)
print(f"    Elapsed training time: {time.time()-START:0.2f}s")

test_loss, test_acc = model.evaluate(data_test, labels_test, verbose=2)
print(f"    Test accuracy: {test_acc:0.5f}")

# --------------------------------- Plotting ----------------------------------

# Plot training history
fig1 = plotlib.training_history_plot(history, 'Event neural network model accuracy')

# Make confsuion matrix
labels_pred = model.predict(data_test)
labels_pred = np.argmax(labels_pred, axis=1)
cm = plotlib.confusion_matrix(labels_test, labels_pred)
class_names = ['signal', 'background']
title = 'Confusion matrix'

# Plot confusion matrix
fig2 = plotlib.confusion_matrix(cm, class_names, title)
