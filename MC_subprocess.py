#!/usr/bin/env python

#from subprocess import Popen, PIPE
import subprocess
import pelita
import numpy as np
import random
import pandas as pd
from multiprocessing import Pool

def test():
    process = Popen(['cat', 'test.py'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print(stdout)

    s = subprocess.check_output(["echo", "Hello World!"])
    print("s = " + str(s))

def run_single(bot1, bot2, seed, new_file=True):
    if new_file:
        mode = 'w+'
    else:
        mode = 'a'

    with open('log.txt', mode) as log, open('seed.txt', mode) as seed_log:
        # print(seed)
        #seed_i = 8263920469466403257
        args = ["pelita", str(bot1), str(bot2) ,"--null", "--seed", str(seed)]
        subprocess.call(args, stdout=log)#, stdin=None, stdout=a, stderr=None, shell=False)
        seed_log.write(str(seed)+'\n')

def seeds_generator(Ngames):
    return np.random.randint(10000000,size=(Ngames))

def run(Ngames,bot1,bot2, seed_list=None):
    seed_list = seeds_generator(Ngames)
    np.savetxt('seed.txt',seed_list, fmt='%d')
    print(seed_list)
    
    with open('log.txt','w') as f:
        for seed_i in seed_list:
            print(seed_i)
            #seed_i = 8263920469466403257
            args = ["pelita", str(bot1), str(bot2) ,"--null", "--seed", str(seed_i)]
            subprocess.call(args,stdout=f)#, stdin=None, stdout=a, stderr=None, shell=False)
    return

def test_seed(seed_i):
    print(seed_i)
    args = ["pelita", "group0.py", "group0.py" ,"--null", "--seed", str(seed_i)]
    subprocess.call(args)#, stdin=None, stdout=a, stderr=None, shell=False)


def log_progress(sequence, every=None, size=None, name='Items'):
    from ipywidgets import IntProgress, HTML, VBox
    from IPython.display import display

    is_iterator = False
    if size is None:
        try:
            size = len(sequence)
        except TypeError:
            is_iterator = True
    if size is not None:
        if every is None:
            if size <= 200:
                every = 1
            else:
                every = int(size / 200)     # every 0.5%
    else:
        assert every is not None, 'sequence is iterator, set every'

    if is_iterator:
        progress = IntProgress(min=0, max=1, value=1)
        progress.bar_style = 'info'
    else:
        progress = IntProgress(min=0, max=size, value=0)
    label = HTML()
    box = VBox(children=[label, progress])
    display(box)

    index = 0
    try:
        for index, record in enumerate(sequence, 1):
            if index == 1 or index % every == 0:
                if is_iterator:
                    label.value = '{name}: {index} / ?'.format(
                        name=name,
                        index=index
                    )
                else:
                    progress.value = index
                    label.value = u'{name}: {index} / {size}'.format(
                        name=name,
                        index=index,
                        size=size
                    )
            yield record
    except:
        progress.bar_style = 'danger'
        raise
    else:
        progress.bar_style = 'success'
        progress.value = index
        label.value = "{name}: {index}".format(
            name=name,
            index=str(index or '?')
        )
    
#test_seed(84)
if __name__ == "__main__":
    run(50,'group0.py','Alessio/group0_alessio.py')
