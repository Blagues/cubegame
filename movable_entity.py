import numpy as np

from entity import Entity


class MovableEntity(Entity):
    def __init__(self, name, id, size, position, max_velocity, drag):

        super().__init__(name, id, size, position)

        self.max_velocity = max_velocity
        self.drag = drag

        self.velocity = np.array([0.0, 0.0], dtype=np.float32)

    def add_velocity(self, vel, dt):
        self.velocity += vel * dt

    def update(self, dt):
        self.velocity = np.clip(self.velocity, -self.max_velocity, self.max_velocity)
        new_position = self.position + self.velocity * dt
        self.velocity *= self.drag

        # bounce
        for i in range(2):
            if new_position[i] < -1 + self.size or new_position[i] > 1 - self.size:
                self.velocity[i] *= -0.8
                new_position[i] = np.clip(new_position[i], -1 + self.size, 1 - self.size)

        self.position = new_position

