import pandas as pd
import numpy as np
import os
import random
import json
import re
import src.utils as utils


class Database:

    def __init__(self):

        self._mode = None
        self._dataset_name = None
        self._data_path = None
        self._dataset_loaded = False

        self._dataset_df = None
        self._groups_df = None
        self._cur_group = None
        self._cur_group_loaded = False
        self._group_index = 0
        self._group_end = 0

        self._data_index = 0

    def load_database(self, data_path, dataset_name, mode='training', resample=False):

        print('Load database. Dataset: {0}. Mode: {1}. Resample: {2}. '.format(
            dataset_name, mode, resample), end='')

        self._mode = mode
        self._dataset_name = dataset_name
        self._data_path = data_path

        if dataset_name == 'IXI-T1':

            if mode not in ['training', 'validation', 'test']:
                raise Exception('Mode must be one of \'training\', \'validation\' or \'test\'')

            if mode != 'training' and resample:
                raise Exception('Resample must be in training mode.')

            if mode == 'training' and resample:
                xls_file = pd.read_excel(data_path + dataset_name + '.xls')
                universe_df = xls_file.loc[:, ['IXI_ID', 'AGE']]
                universe_df.dropna(how='any', inplace=True)
                universe_df.index = universe_df['IXI_ID']
                universe_df.drop('IXI_ID', axis=1, inplace=True)
                universe_df.sort_values(by=['AGE'], inplace=True)

                training_df = universe_df.sample(frac=0.7)
                rest_df = universe_df.loc[universe_df.index.difference(training_df.index)]
                validation_df = rest_df.sample(frac=0.5)
                test_df = rest_df.loc[rest_df.index.difference(validation_df.index)]

                training_df.to_csv(data_path + 'training_df.csv')
                validation_df.to_csv(data_path + 'validation_df.csv')
                test_df.to_csv(data_path + 'test_df.csv')

            if mode == 'training':
                self._dataset_df = pd.read_csv(data_path + 'training_df.csv')

            if mode == 'validation':
                self._dataset_df = pd.read_csv(data_path + 'validation_df.csv')

            if mode == 'test':
                self._dataset_df = pd.read_csv(data_path + 'test_df.csv')

            self._data_index = 0
            self._dataset_loaded = True

            if mode == 'training' and resample:
                self._create_groups()

            self._groups_df = pd.read_csv(data_path + 'groups.csv')
            self._group_index = self._groups_df['GROUP_AGE'].min()
            self._group_end = self._groups_df['GROUP_AGE'].max() + 1
            self._cur_group_loaded = False

            print('Done.')

        else:
            raise Exception(dataset_name + ' dataset is not found.')

    def _create_groups(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        if self._mode != 'training':
            raise Exception('Create groups function must be run in training mode.')

        if self._dataset_name == 'IXI-T1':

            groups = pd.DataFrame(columns=['IXI_ID', 'AGE', 'GROUP_AGE'])

            min_age = int(self._dataset_df.loc[:, 'AGE'].min())
            max_age = int(self._dataset_df.loc[:, 'AGE'].max())

            for age in range(min_age, max_age):
                age_span = 0
                sample_size = 0
                sample_result = None

                while sample_size < 5:
                    age_span += 1
                    query_str = 'AGE > {0} and AGE < {1}'.format(age - age_span, age + age_span)
                    sample_result = self._dataset_df.query(query_str)
                    sample_size = sample_result.shape[0]

                sample_result['GROUP_AGE'] = age
                groups = groups.append(sample_result)

            groups.index = groups['IXI_ID']
            groups.drop('IXI_ID', axis=1, inplace=True)
            groups.to_csv(self._data_path + 'groups.csv')

        else:
            raise Exception(self._dataset_name + ' dataset is not found.')

    def get_group_end(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        return self._groups_df['GROUP_AGE'].max() + 1

    def get_data_from_group_size(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        if self._cur_group_loaded is False:
            raise Exception('Current group must be loaded first.')
        return self._cur_group.shape[0]

    def get_data_index(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        return self._data_index

    def set_data_index(self, id):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        self._data_index = id

    def get_group_index(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        return self._group_index

    def set_group_index(self, id):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        self._group_index = id

    def get_next_group(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')
        if self._group_index >= self._group_end:
            return None

        query_str = 'GROUP_AGE == {0}'.format(self._group_index)
        self._cur_group = self._groups_df.query(query_str)
        self._group_index += 1
        self._data_index = 0
        self._cur_group_loaded = True

        return self._cur_group

    def has_next_data_from_group(self):
        if self._data_index < self._cur_group.shape[0]:
            return True
        else:
            return False

    def get_next_data_from_group(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')

        if self._cur_group is None:
            raise Exception('Call get_next_group() first.')

        if self._mode != 'training':
            raise Exception('get_next_data_from_group must be called in training mode.')

        if self.has_next_data_from_group() is False:
            return None

        row_series = self._cur_group.iloc[self._data_index]
        data_id = str(int(row_series['IXI_ID']))
        data = np.load(self._data_path + self._dataset_name + '/' + data_id + '.npy')

        self._data_index += 1

        return data_id, data, row_series['AGE']

    def has_next_data_from_dataset(self):
        if self._data_index < self._dataset_df.shape[0]:
            return True
        else:
            return False

    def get_next_data_from_dataset(self):
        if self._dataset_loaded is False:
            raise Exception('Dataset must be loaded first.')

        if self.has_next_data_from_dataset() is False:
            return None

        if self._mode != 'validation' or self._mode != 'test':
            raise Exception('get_next_data must be called in validation or test mode.')

        data_name, age = self._dataset_df.iloc[self._data_index, ['IXI-T1', 'AGE']]
        self._data_index += 1

        data = np.load(self._data_path + self._dataset_name + '/' + data_name + '.npy')

        return data_name, data, age

if __name__ == '__main__':

    database = Database()
    database.load_database('../../data/', 'IXI-T1', mode='training', resample=False)
    database.get_next_group()
    database.get_next_data_from_group()
    database.get_data_index()