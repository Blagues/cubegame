import numpy as np


class Entity:
    def __init__(self, name, id, size, position=np.array([0.0, 0.0], dtype=np.float32)):
        self.name = name
        self.id = id
        self.size = size
        self.position = position

    def __str__(self):
        return f"{self.name} ({self.id})"