import os
import torch
from torch.autograd import Variable
import torch.nn as nn
import torch.optim as optim
import torch.backends.cudnn as cudnn

from src.Net import Net
from src.Database import Database


def train_model(net, database):

    # criterion = nn.CrossEntropyLoss()
    criterion = nn.MSELoss()
    optimizer = optim.SGD(net.parameters(), lr=1e-5, momentum=0.9)

    for epoch in range(100):

        database.reset_training_index()
        running_loss = 0

        while database.has_training_next():

            img_name, img_tensor, age_tensor = database.load_training_data_next()
            print(database.get_training_index(), img_name)
            img_tensor = img_tensor.unsqueeze(0).unsqueeze(0).float()
            img_tensor = Variable(img_tensor.cuda())
            age_tensor = age_tensor.float()
            age_tensor = Variable(age_tensor.cuda())

            output = net(img_tensor)
            print('output: ', output)
            print('target: ', age_tensor)
            optimizer.zero_grad()
            loss = criterion(output, age_tensor)
            loss.backward()
            optimizer.step()

            running_loss += loss.data[0]

            if database.get_training_index() % 1 == 0:
                print('Epoch: %d, Data: %d, Loss: %.3f' % (epoch, database.get_training_index(), loss.data[0]))

            # if database.get_training_index() % 100 == 99:
            #     break

        torch.save(net, 'net.pkl')

        data_size = database.get_training_data_size()
        running_loss /= data_size
        print('=== Epoch: %d, Datasize: %d, Average Loss: %.3f' % (epoch, data_size, running_loss))


def main():
    print('Load database.')
    database = Database()
    database.load_database('IXI-T1', (128, 128, 75))

    if os.path.exists(r'net.pkl'):
        print('Construct net. Load from pkl file.')
        net = torch.load('net.pkl')
    else:
        print('Construct net. Create a new network.')
        net = Net()
    net.cuda()

    print('Start training.')
    train_model(net, database)

if __name__ == '__main__':
    cudnn.enabled = False
    main()
