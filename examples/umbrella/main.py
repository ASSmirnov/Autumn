from pathlib import Path
import sys

from interfaces import IConsumer


path = Path(__file__).parents[2]
sys.path.append(str(path))
from consumer import *
from client import *
from execution import *
from helpers import *

from autumn.public import dm

dm.init_profiles("prod", "system", "umbrella")
dm.init(test_mode=True)
dm.start()
consumer = dm.get_instance(IConsumer)
consumer.poll()




# dm.clear()
# dm.init_profiles("local", "prod")
# dm.init_property("credentials", "user=admin,password=qwerty")
# dm.start()
# umbrella_client = dm.get_instance(UmbrellaClient)
# print("Response ", umbrella_client.request())

