from pathlib import Path
import sys


path = Path(__file__).parents[3]
sys.path.append(str(path))
from autumn.public import dm

from examples.umbrella.client import *
from examples.umbrella.execution import *
from examples.umbrella.helpers import *
from .task import *

dm.init(test_mode=True)
dm.init_profiles("test")
dm.start()