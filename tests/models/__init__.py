from cProfile import run
from tests.models.thing_tests import run_all_thing_tests


def run_all_model_tests():
    run_all_thing_tests()


