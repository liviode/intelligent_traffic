import sys

import os

#print(os.getcwd())
model_name = sys.argv[1]
type=sys.argv[2]


#model_name='model_03'
#type = 'sample'

file_name='outdata/'+model_name+'_'+type+'.txt'



f = open(file_name)
data = f.read()
data2 = data.split("\n")
data = []
for x in data2:
    if x != '':
        data.append(int(x))

import matplotlib.pyplot as plt

plt.plot(data)
plt.ylabel(model_name + ' ('+type+')')
plt.show()

