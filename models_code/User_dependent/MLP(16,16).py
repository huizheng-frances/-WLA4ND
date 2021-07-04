"""
Keras LSTM, multi-task & multi-outputs prediction (also can be used in multi-label situation)

"""

from numpy.random import seed
seed(1)
# from tensorflow import set_random_seed
# set_random_seed(2)

import pandas as pd
import numpy as np
from numpy import concatenate
from pandas import DataFrame
from pandas import concat
from sklearn.preprocessing import MinMaxScaler
import keras
from keras.layers import Input, Embedding, LSTM, Dense
from pandas import read_csv
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
from keras.models import Model
from keras.layers.core import *
import helper_funcs
from sklearn.metrics import confusion_matrix
import seaborn as sns
import os
import warnings
import glob
import numpy

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' #Hide messy TensorFlow warnings
warnings.filterwarnings("ignore") #Hide messy Numpy warnings



def build_model(trainX,task_num, shared_layer,dense_num, n_labels):

    """
    Keras Function model
    """
    concate_list = []
    input_list = []
    for i in range(0, task_num):
        locals()['input' + str(i)] = Input(shape=(trainX[i].shape[1], trainX[i].shape[2]),
            name='input' + str(i))
        locals()['dense_out' + str(i)] = Dense(dense_num, activation='relu')(locals()['input' + str(i)])
        concate_list.append(locals()['dense_out' + str(i)])
        input_list.append(locals()['input' + str(i)])

    concate_layer = keras.layers.concatenate(concate_list)
    dense_shared = Dense(shared_layer, activation='relu')(concate_layer)

    output_list = []
    for i in range(0, task_num):
        locals()['sub' + str(i)] = Dense(dense_num, activation='relu')(dense_shared)
        locals()['sub' + str(i)] = Flatten()(locals()['sub' + str(i)])
        locals()['out' + str(i)] = Dense(n_labels, activation='sigmoid')(locals()['sub' + str(i)])
        output_list.append(locals()['out' + str(i)])

    model = Model(inputs=input_list, outputs=output_list)
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['binary_accuracy'])
    print(model.summary())
    return model

def confu_matrix_plot(true_multiclass,pred_multiclass,i):
    labels = ['read', 'writeQA', 'write','type', 'rest', 'off']
    # labels_rever = ['off', 'rest', 'type','write', 'wr', 'read']

    cm = confusion_matrix(true_multiclass, pred_multiclass,labels)
    fig = plt.figure()
    ax = fig.add_subplot(111)

    sns.heatmap(cm/np.sum(cm), annot=True, fmt=".2%",ax=ax,cmap='Blues')  # annot=True to annotate cells

    ax.set_xlabel('Predicted labels')
    ax.set_ylabel('True labels')
    ax.xaxis.set_label_position('top')

    # ax.set_title('Confusion Matrix')
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.xaxis.set_ticks_position('top')

    plt.savefig('results/confusion_matrix_MLP_'+str(i)+'.png', dpi=150)

def confu_matrix_save(true_multiclass,pred_multiclass):
    labels = ['read', 'writeQA', 'write','type', 'rest', 'off']
    cm = confusion_matrix(true_multiclass, pred_multiclass,labels)
    return cm

def main():
    # network parameters
    task_num = 8
    shared_layer = 576
    dense_num = 16

    look_back = 10  # number of previous timestamp used for training
    n_columns = 71  # total columns
    n_labels = 6  # number of labels
    split_ratio = 0.8  # train & test data split ratio

    trainX_list = []
    trainy_list = []
    testX_list = []
    testy_list = []
    file_list = glob.glob('data8p/processed/*.csv')
    # print (file_list[0])

    for i in range(len(file_list)):
        locals()['dataset' + str(i)] = file_list[i]
        locals()['dataset' + str(i)], locals()['scaled' + str(i)], locals()['scaler' + str(i)] = helper_funcs.load_dataset(
            locals()['dataset' + str(i)])
        locals()['train_X' + str(i)], locals()['train_y' + str(i)], locals()['test_X' + str(i)], locals()[
            'test_y' + str(i)] = helper_funcs.split_dataset(locals()['dataset' + str(i)], locals()['scaled' + str(i)], look_back,
                                               n_columns, n_labels, split_ratio)
        trainX_list.append(locals()['train_X' + str(i)])
        trainy_list.append(locals()['train_y' + str(i)])
        testX_list.append(locals()['test_X' + str(i)])
        testy_list.append(locals()['test_y' + str(i)])

    model = build_model(trainX_list,task_num, shared_layer, dense_num, n_labels)


    import time
    start_time = time.time()

    # fit network
    history = model.fit(trainX_list, trainy_list,
                        epochs=100,
                        batch_size=50,
                        # validation_split=0.25,
                        validation_data=(testX_list, testy_list),
                        verbose=2,
                        shuffle=False,
                        callbacks=[
                            keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=25, verbose=2,
                                                          mode='min')]
                        )
    end_time = time.time()
    print('--- %s seconds ---' % (end_time - start_time))

    # make prediction
    pred_time = time.time()

    y_pred1, y_pred2, y_pred3, y_pred4, y_pred5, y_pred6, y_pred7, y_pred8 = model.predict(testX_list)

    pred_end_time = time.time()

    #=====================================================================================#
    # write parameters & results to file
    # file = open('results/Baseline_results(6)_F1.txt', 'w')
    file = open('results/M_MLP(16,16).txt', 'w')

    file.write('task_num:' + str(task_num) + '\n')
    file.write('shared_layer:' + str(shared_layer) + '\n')
    file.write('dense_num:' + str(dense_num) + '\n')
    file.write('running time:' + str(end_time - start_time) + '\n')

    sum_bacc = 0
    sum_re = 0
    sum_pre = 0
    sum_F1 = 0
    sum_acc = 0
    # balance accuracy
    for i in range(len(file_list)):
        locals()['Bacc' + str(i)] = helper_funcs.evaluation(locals()['test_X' + str(i)], locals()['test_y' + str(i)], locals()['y_pred' + str(i+1)],
                                               look_back, n_columns, n_labels, locals()['scaler' + str(i)])
        sum_bacc = sum_bacc + (locals()['Bacc' + str(i)])[0]
        sum_F1 = sum_F1 + (locals()['Bacc' + str(i)])[1]
        sum_pre = sum_pre + (locals()['Bacc' + str(i)])[2]
        sum_re = sum_re + (locals()['Bacc' + str(i)])[3]
        sum_acc = sum_acc + (locals()['Bacc' + str(i)])[4]

        file.write('BA:' + ' ' + str((locals()['Bacc' + str(i)])[0]) + ' ')
        file.write('F1:' + ' ' + str((locals()['Bacc' + str(i)])[1]) + ' ')
        file.write('precision:' + ' ' + str((locals()['Bacc' + str(i)])[2]) + '\n')
        file.write('recall:' + ' ' + str((locals()['Bacc' + str(i)])[3]) + '\n')
        file.write('accuracy:' + ' ' + str((locals()['Bacc' + str(i)])[4]) + '\n')
        confu_matrix_plot((locals()['Bacc' + str(i)])[5],(locals()['Bacc' + str(i)])[6],i)

        confu_matrix = confu_matrix_save((locals()['Bacc' + str(i)])[5], (locals()['Bacc' + str(i)])[6])
        print(confu_matrix)
        numpy.savetxt("confu_matrix/confusion_matrix_MLP1616_" + str(i) + ".csv", X=confu_matrix.astype(int),
                      delimiter=', ',
                      fmt='%.0f')
        confu_matrix = confu_matrix / np.sum(confu_matrix) * 1000
        print(confu_matrix)
        numpy.savetxt("confu_matrix/confusion_matrix_MLP1616-" + str(i) + "-nor.csv", X=confu_matrix.astype(float),
                      delimiter=', ',
                      fmt='%.00f')

    file.write('avg_bacc: ' + str(sum_bacc / len(file_list)) + '\n')
    file.write('avg_TPR: ' + str(sum_re / len(file_list)) + '\n')
    file.write('avg_precision: ' + str(sum_pre / len(file_list)) + '\n')
    file.write('avg_F1: ' + str(sum_F1 / len(file_list)) + '\n')
    file.write('avg_accuracy: ' + str(sum_acc / len(file_list)) + '\n')
    file.write('training time:' + str(end_time - start_time))
    file.write('prediction time:' + str(pred_end_time - pred_time))
    
if __name__ == '__main__':
    main()


