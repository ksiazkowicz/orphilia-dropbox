import time, orphilia, orphiliaclient, Queue
from shared import path_rewrite

configurationDirectory = orphilia.common.getConfigurationDirectory()


def monitor():
    try:
        while True:
            tmp = ['delta']
            orphiliaclient.client.client(tmp)
            time.sleep(60)

        while not q.empty():
            print q.get()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
