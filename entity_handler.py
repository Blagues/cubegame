from entity import Entity


class EntityHandler:
    def __init__(self):
        self.entities = []

    def add_entity(self, entity: Entity):
        self.entities.append(entity)

    def update(self, dt):
        for entity in self.entities:
            entity.update(dt)
