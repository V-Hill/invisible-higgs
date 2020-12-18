# -*- coding: utf-8 -*-
"""
This file contains Classes for preparing the data for input into the neural 
networks.
"""

# Python libraries
import pandas as pd
import numpy as np
from sklearn import preprocessing

class DataProcessing():
    def __init__(self, data):
        self.data_list = data.data
        self.data = None
        self.all_columns = []
        
        self.merge_data_list()
        
    def merge_data_list(self):
        self.data = pd.concat(self.data_list, axis=0, ignore_index=True)
        self.all_columns = list(self.data.columns.values)
        
    #--------------------------------------------------------------------------
    
    def label_signal_noise(self, signal_list):
        """
        This function converts the dataset labels to one of two numeric values
        representing either signal or noise (0 or 1). 

        Parameters
        ----------
        signal_list : list
            List of df['dataset'] values to consider signal.
            e.g. ['ttH125']
        """
        label_dict = {}
        signal_label = 'inv_signal'
        noise_label = 'noise'
        
        for df in self.data_list:
            dataset = df.iloc[0]['dataset']
            if dataset in signal_list:
                label_dict[dataset] = signal_label
            else:
                label_dict[dataset] = noise_label
        labels = self.data['dataset']
        labels = labels.replace(label_dict)
        self.data['dataset'] = labels
        
    def return_dataset_labels(self):
        labels = self.data['dataset'].copy(deep=False)
        return labels.values.astype(str)
    
    def set_dataset_labels(self, event_labels):
        self.data['dataset'] = event_labels
        
    #--------------------------------------------------------------------------
    
    def get_event_columns(self, columns_to_ignore, verbose=True):
        """
        This function generates a list of the columns to be used in the 
        training data for the event level variables. 
    
        Parameters
        ----------
        columns_to_ignore : list
            List of columns to explicitly exclude
    
        Returns
        -------
        columns_filtered : list
            list of columns to use for training
        """
        print("columns to be used for event level neural network:")
        columns_filtered = []
        
        for idx, col in enumerate(self.all_columns):
            if isinstance(self.data[col].iloc[idx], (np.float32, np.float64, np.int64, np.uint32)):
                if col not in columns_to_ignore:
                    columns_filtered.append(col)
                    if verbose:
                        print(f"    {col:<32}: {self.data[col].dtypes}")
        return columns_filtered

    def get_jet_columns(self, verbose=True):
        """
        This function generates a list of the columns to be used in the 
        training data for the jet variables.

        Returns
        -------
        columns_filtered : list
            list of columns to use for training
        """
        columns_filtered = []
        
        for col in self.all_columns:
            if isinstance(self.data[col].iloc[0], np.ndarray):
                columns_filtered.append(col)
                if verbose:
                    print(f"    {col:<32}: {self.data[col].dtypes}")
        return columns_filtered
    
    def filter_data(self, column_filter):
        """
        Remove all columns from the self.data dataframe except those in the
        list column_filter.

        Parameters
        ----------
        column_filter : list
            list of columns in the new self.data
        """
        self.data = self.data[column_filter]
 
    def set_nan_to_value(self, column, val=0):
        self.data.fillna({column: val})
    
    def remove_nan(self, column):
        pass


class LabelMaker():
    """
    This Class contains functions for creating numeric labels for the training
    categories. Encodes categorical values to intergers.
    """
    def label_encoding(label_data, verbose=True):
        encoder = preprocessing.LabelEncoder()
        labels = encoder.fit_transform(label_data)
        if verbose:
            keys = encoder.classes_
            values = encoder.transform(keys)
            print(f"label encoding: {dict(zip(keys, values))}")
        return labels
    
    def onehot_encoding(data_list, verbose=True):
        data_list = data_list.reshape(-1, 1)
        
        onehot_encoder = preprocessing.OneHotEncoder(sparse=False)
        labels = onehot_encoder.fit_transform(data_list)
        if verbose:
            keys = onehot_encoder.categories_[0]
            values = onehot_encoder.inverse_transform(keys)
            print(dict(zip(keys, values)))
            print(keys, values)
            
        return labels


class WeightMaker():
    """
    This Class contains functions for creating the class weights and sample
    weights to be added to the neural network.
    """
    def event_class_weights(data):
        """
        This function creates a dictionary of class weights. The weights are
        calculated from the number of events of each classification label.

        Parameters
        ----------
        data : DataProcessing

        Returns
        -------
        class_weights : dict
        """
        weight_nominal_vals = data.data['weight_nominal']
        total_events = len(weight_nominal_vals)
        print(f"total number of events: {total_events}")
        
        unique_labels = data.data['dataset'].unique()
        class_weights = []
        
        for label in unique_labels:
            weight_selection = data.data.loc[data.data['dataset'] == label]['weight_nominal']
            weight = total_events/len(weight_selection)
            print(f"    {total_events}/{len(weight_selection)} = {weight:0.3f}")
            class_weights.append(weight)
            
        class_weight_dict = dict(zip(unique_labels, class_weights))
        print(f"class weights: {class_weight_dict}")
        return class_weight_dict
        

    def weight_nominal_sample_weights(data):
        """
        This function uses the 'weight_nominal' parameter to create an event
        by event sample_weight. The sample weights are normalised based on the
        sum of the 'weight_nominal' for each classification label.

        Parameters
        ----------
        data : DataProcessing

        Returns
        -------
        new_weights : np.ndarray
            Array containing the sample weights to be fed into the model.fit()
        """
        weight_nominal_vals = data.data['weight_nominal']
        total_weight_nominal = weight_nominal_vals.sum()
        print(f"total weight_nominal: {total_weight_nominal}")
        
        unique_labels = data.data['dataset'].unique()
        weight_nominals_list = []
        
        for label in unique_labels:
            weight_selection = data.data.loc[data.data['dataset'] == label]['weight_nominal']
            normalisation = total_weight_nominal/weight_selection.sum()
            weight_selection *= normalisation
            
            print(f"    {total_weight_nominal}/{weight_selection.sum()} = {normalisation:0.3f}")
            weight_nominals_list.append(weight_selection)
            
        new_weights = pd.concat(weight_nominals_list, axis=0, ignore_index=True)
        return new_weights.values
    
def split_data(event_data, labels, weights, test_size, shuffle=True):
    """
    This function splits a numpy array containg event data into test 
    and train sets matched with the right labels.
    
    Parameters
    ----------
    event_data : np.darray
        Event data in a (m,n) array where m is the different simulated event 
        data and n is the features from an event.
    labels : np.darray
        The labels that correspond to the different events
    weights : np.darray
        The weights for each event to control for cross section of different 
        events
    test_size : float
        The fraction of the data that is test data
    shuffle : bool, optional
        True if you want the data shuffled
        
    Results
    -------
    training_data : list 
        Data in a [(m,n),l,w] list where l is the label for an event and w is 
        weight. If shuffle is true then the events have been shuffled. This
        data is to be trained on.
    test_data : list 
        Data in a [(m,n),l,w] this data is for a network to be tested on.
    """
    if shuffle is True:    
        #Shuffle the training data by the same amount
        rng_state = np.random.get_state()
        
        np.random.shuffle(event_data)
        np.random.set_state(rng_state)
        
        np.random.shuffle(labels)
        np.random.set_state(rng_state)
        
        np.random.shuffle(weights)
        #test data does not need to be shuffled
    
    else:
        pass
    
    train_length = int(len(event_data)*(1-test_size))
    
    training_data = event_data[:train_length,]
    training_label = labels[:train_length]
    training_weight = weights[:train_length]

    test_data = event_data[train_length:,]
    test_label = labels[train_length:]
    test_weight = weights[train_length:]
    
    training_data = [training_data,
                     training_label,
                     training_weight]
    
    test_data = [test_data,
                 test_label,
                 test_weight]
    
    return training_data, test_data
