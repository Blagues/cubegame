import numpy as np


class Entity:
    def __init__(self, name, id, size, position=np.array([0.0, 0.0], dtype=np.float32)):
        self.name = name
        self.id = id
        self.size = size
        self.position = position

    def clip_to_screen(self):
        # Clip the position to keep the entity within the screen boundaries
        self.position = np.clip(self.position, -1 + self.size, 1 - self.size)

    def update(self, dt):
        pass

    def __str__(self):
        return f"{self.name} ({self.id})"