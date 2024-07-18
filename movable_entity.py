import numpy as np
from entity import Entity


class MovableEntity(Entity):
    def __init__(self, name, texture, id, size, position, max_velocity, drag):
        super().__init__(name, texture, id, size, position)
        self.max_velocity = max_velocity
        self.drag = drag
        self.velocity = np.array([0.0, 0.0], dtype=np.float32)
        self.default_size = np.array([0.1, 0.1], dtype=np.float32)  # Add a default size

    def add_velocity(self, vel, dt):
        self.velocity += vel * dt

    def update(self, dt):
        self.velocity = np.clip(self.velocity, -self.max_velocity, self.max_velocity)

        new_position = self.position + self.velocity * dt
        self.velocity *= self.drag

        # if velocity is less than 1e-2, set it to 0
        self.velocity = np.where(np.abs(self.velocity) < 1e-2, 0, self.velocity)

        size = self.size if self.size is not None else self.default_size  # Use default size if size is None

        for axis in range(2):
            if self.hit_wall(axis, size):
                self.velocity[axis] *= 0
                new_position[axis] = np.clip(new_position[axis], -1 + size[axis] / 2, 1 - size[axis] / 2)

        self.position = new_position

    def hit_wall(self, axis, size):
        return self.position[axis] < -1 + size[axis] / 2 or self.position[axis] > 1 - size[axis] / 2
