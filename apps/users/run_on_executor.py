import tornado
from tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import time

class Test():
    executor = ThreadPoolExecutor(100)

    @run_on_executor
    def longTimeTask(self):
        print( "go to sleep")
        time.sleep(2)
        print("wake up")


if __name__ == "__main__":
    test = Test()
    test.longTimeTask()
    i=1
    while(i<=5000):
        test.longTimeTask()
        i = i+1


    print("print very soon")
