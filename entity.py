import numpy as np


class Entity:
    def __init__(self, name, texture, id, size, position=np.array([0.0, 0.0], dtype=np.float32)):
        self.name = name
        self.id = id
        self.size = size
        self.position = position
        self.texture = texture

    def update(self, dt):
        pass

    def __str__(self):
        return f"{self.name} ({self.id})"