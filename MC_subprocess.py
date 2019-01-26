#!/usr/bin/env python

#from subprocess import Popen, PIPE
import subprocess
import pelita
import numpy as np
import random
import pandas as pd

def test():
    process = Popen(['cat', 'test.py'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print(stdout)

    s = subprocess.check_output(["echo", "Hello World!"])
    print("s = " + str(s))

def run(Ngames,bot1,bot2):
    directory = '/home/student/ASPP/group0/'
    f  = open(directory+'log.txt','w')
    seed_list = np.random.randint(100,size=(Ngames))
    print(seed_list)
    for seed_i in seed_list:
        print(seed_i)
        #seed_i = 8263920469466403257
        args = ["pelita", str(bot1), str(bot2) ,"--null", "--seed", str(seed_i)]
        subprocess.call(args,stdout=f)#, stdin=None, stdout=a, stderr=None, shell=False)
    f.close()
    np.savetxt('seed.txt',seed_list, fmt='%d')
def test_seed(seed_i):
    print(seed_i)
    args = ["pelita", "group0.py", "group0.py" ,"--null", "--seed", str(seed_i)]
    subprocess.call(args)#, stdin=None, stdout=a, stderr=None, shell=False)

#test_seed(84)
run(5,'group0.py','demo02_random.py')
