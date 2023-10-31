from pathlib import Path
import json
import sys


path = Path(__file__).parents[2]
sys.path.append(str(path))

from client import *
from execution import *
from helpers import *

from autumn.public import dm

def print_help():
    print("Usage: python main.py [system, local]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        sys.exit(1)
    execution_type = sys.argv[1]
    if execution_type == "system":
        from consumer import *
        from interfaces import IConsumer
        dm.init_profiles("prod", "system", "umbrella")
        dm.start()
        consumer = dm.get_instance(IConsumer)
        consumer.poll()
    elif execution_type == "local":
        from local_run import *
        with open(path / "examples" / "umbrella" / "resources" / "task.json") as f:
            task = json.load(f)
        dm.init_profiles("prod", "local")
        dm.init_property("task", task)
        dm.start()
        executor = dm.get_instance(IExecutor)
        executor.execute()    
    else:
        print_help()
        sys.exit(1)