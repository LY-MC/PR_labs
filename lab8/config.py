from raft import RAFTFactory
import time
import random
import sys

service_info = {
    "host": "127.0.0.1",
    "port": int(sys.argv[1])
}

time.sleep(random.randint(1, 3))
node = RAFTFactory(service_info)
print(node.to_string())
