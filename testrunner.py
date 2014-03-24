import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

from django.test.utils import get_runner
from django.conf import settings


def run_tests():
    cls = get_runner(settings)
    runner = cls()
    failures = runner.run_tests(['tests'])
    sys.exit(failures)


if __name__ == '__main__':
    run_tests()
