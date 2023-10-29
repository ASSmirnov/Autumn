from pathlib import Path
import sys

path = Path(__file__).parents[2]
sys.path.append(str(path))

from client.types import UmbrellaClient
from client.user_credentials_client import UserCredentialClient
from client.system_client import SystemClient

from autumn.public import dm

dm.init_profiles("prod", "system")
dm.init(test_mode=True)
dm.start()
umbrella_client = dm.get_instance(UmbrellaClient)
print("Response ", umbrella_client.request())

dm.clear()
dm.init_profiles("local", "prod")
dm.init_property("credentials", "user=admin,password=qwerty")
dm.start()
umbrella_client = dm.get_instance(UmbrellaClient)
print("Response ", umbrella_client.request())