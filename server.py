from multiprocessing import Process, Manager, Pool

def logger():
    print('logger process started')
    while True:
        pass


if __name__ == '__main__':
    print("hi")
    #pool = Pool(processes=4)
    #pool.apply_async(logger)
    Process(target=logger).start()
    Process(target=logger).start()
    Process(target=logger).start()
    Process(target=logger).start()
    Process(target=logger).start()
    Process(target=logger).start()

    print("hello")