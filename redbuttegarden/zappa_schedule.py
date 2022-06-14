# As suggested by https://github.com/Miserlou/Zappa/issues/1123#issuecomment-398762606

class Runner:
    def __getattr__(self, attr):
        from django.core.management import call_command
        return lambda: call_command(attr)

import sys
sys.modules[__name__] = Runner()
