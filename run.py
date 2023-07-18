import threading, os
def f1():
    os.system("python main.py")
def f2():
    os.system("python wind.py")
t1 = threading.Thread(target=f1)
t2 = threading.Thread(target=f2)
t1.start()
t2.start()