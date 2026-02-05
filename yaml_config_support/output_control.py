from collections import OrderedDict

class OutputControl:
    def __init__(self, verbose=False):
        self.verbose = verbose

    def out(self, *args):
        if self.verbose:
            print('LOG ' + ' '.join(args))
