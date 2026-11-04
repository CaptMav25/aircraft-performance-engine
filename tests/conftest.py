# Lets the tests import the project modules (units, aircraft, ...) from the folder above.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
