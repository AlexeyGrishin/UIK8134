import random

random.seed(1)


class Randomizer:
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def __float__(self):
        return random.uniform(self.min, self.max)


def random_between(min, max):
    return Randomizer(min, max)
