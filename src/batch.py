import subprocess
import os
import nilearn.image as ni_img
import re
import numpy as np


def get_unused_list():
    f = open('unused_list.txt', 'w')

    data_list = os.listdir('data/IXI-T1-unused')
    for name in data_list:
        print(name, file=f)
    f.close()


def rm_unused_data():
    f = open('../data/IXI-T1-unused_list.txt', 'r')

    for line in f:
        subprocess.call('rm ../data/IXI-T1-raw/' + line.strip(), shell=True)

    f.close()


def resize_data():

    data_name_list = os.listdir('../data/IXI-T1-raw')
    for name in data_name_list:
        re_result = re.findall(r'IXI(\d+)-', name)
        img_id = int(re_result[0])
        img = ni_img.load_img('../data/IXI-T1-raw/' + name).get_data()

        new_shape = (128, 128, 75)
        resize_rate = [new_shape[0]/img.shape[0], new_shape[1]/img.shape[1], new_shape[2]/img.shape[2]]
        print(name, img.shape)
        new_img = np.zeros(shape=new_shape, dtype='int16')
        for x in range(new_shape[0]):
            for y in range(new_shape[1]):
                for z in range(new_shape[2]):
                    old_x = int(x / resize_rate[0])
                    old_y = int(y / resize_rate[1])
                    old_z = int(z / resize_rate[2])
                    data = 1.0/8 * (float(img[old_x, old_y, old_z]) + float(img[old_x, old_y, old_z+1]) +
                                    float(img[old_x, old_y+1, old_z]) + float(img[old_x, old_y+1, old_z+1]) +
                                    float(img[old_x+1, old_y, old_z]) + float(img[old_x+1, old_y, old_z+1]) +
                                    float(img[old_x+1, old_y+1, old_z]) + float(img[old_x+1, old_y+1, old_z+1]))
                    data0 = img[old_x, old_y, old_z]
                    # if (data != 0) :
                    #     print(data, data0)
                    new_img[x, y, z] = data
        # print(new_img.mean())
        # print(new_img.max())
        # print(new_img.min())
        # print(img.mean())
        # print(img.max())
        # print(img.min())
        # new_img = new_img - new_img.mean()

        np.save('../data/IXI-T1/' + str(img_id), new_img)


if __name__ == '__main__':
    resize_data()