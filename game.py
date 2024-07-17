import glfw
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from PIL import Image
import ctypes

from movable_entity import MovableEntity


class Game:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.entities = []
        self.user_entity = None
        self.last_time = 0

    def init_glfw(self):
        if not glfw.init():
            raise Exception("GLFW cannot be initialized")

        self.window = glfw.create_window(self.width, self.height, "GLFW OpenGL PNG Images", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window cannot be created")

        glfw.set_window_pos(self.window, 100, 100)
        glfw.make_context_current(self.window)

    def load_texture(self, file_path):
        try:
            image = Image.open(file_path).convert("RGBA")
        except IOError:
            print(f"Error: Unable to open the image file: {file_path}")
            return None

        image_data = image.tobytes()
        width, height = image.size

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        if glGetError() != GL_NO_ERROR:
            print(f"OpenGL error occurred while loading texture: {file_path}")
            return None

        return texture, (width, height)

    def add_entity(self, file_path, name, position, max_velocity=np.array([15, 15]), drag=(0.9, 0.9), is_user=False):
        texture_info = self.load_texture(file_path)
        if texture_info is None:
            print(f"Failed to load texture for entity: {name}")
            return

        texture, (width, height) = texture_info
        size = (width / self.width, height / self.height)  # Normalize size to screen coordinates
        size = (size[0] * 4, size[1] * 4)  # Scale the size up

        id = len(self.entities)

        entity = MovableEntity(name, texture, id, size, position, max_velocity, drag)

        self.entities.append(entity)

        if is_user:
            self.user_entity = entity

    def process_input(self, dt):
        if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(self.window, True)

        if self.user_entity:
            move_force = 5
            if glfw.get_key(self.window, glfw.KEY_LEFT) == glfw.PRESS:
                self.user_entity.add_velocity(np.array([-move_force, 0]), dt)
            if glfw.get_key(self.window, glfw.KEY_RIGHT) == glfw.PRESS:
                self.user_entity.add_velocity(np.array([move_force, 0]), dt)
            if glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS:
                self.user_entity.add_velocity(np.array([0, move_force]), dt)
            if glfw.get_key(self.window, glfw.KEY_DOWN) == glfw.PRESS:
                self.user_entity.add_velocity(np.array([0, -move_force]), dt)

    def check_collision(self, entity1, entity2):
        return (abs(entity1.position[0] - entity2.position[0]) < (entity1.size[0] + entity2.size[0]) / 2 and
                abs(entity1.position[1] - entity2.position[1]) < (entity1.size[1] + entity2.size[1]) / 2)

    def handle_collision(self, entity1, entity2):
        overlap_x = (entity1.size[0] + entity2.size[0]) / 2 - abs(entity1.position[0] - entity2.position[0])
        overlap_y = (entity1.size[1] + entity2.size[1]) / 2 - abs(entity1.position[1] - entity2.position[1])

        if overlap_x < overlap_y:
            if entity1.position[0] < entity2.position[0]:
                entity1.position[0] -= overlap_x / 2
                entity2.position[0] += overlap_x / 2
            else:
                entity1.position[0] += overlap_x / 2
                entity2.position[0] -= overlap_x / 2
        else:
            if entity1.position[1] < entity2.position[1]:
                entity1.position[1] -= overlap_y / 2
                entity2.position[1] += overlap_y / 2
            else:
                entity1.position[1] += overlap_y / 2
                entity2.position[1] -= overlap_y / 2

    def run(self):
        vertex_shader = """
        #version 120
        attribute vec2 position;
        attribute vec2 texcoord;
        varying vec2 v_texcoord;
        uniform vec2 translation;
        uniform vec2 scale;
        void main() {
            gl_Position = vec4(position * scale + translation, 0.0, 1.0);
            v_texcoord = texcoord;
        }
        """

        fragment_shader = """
        #version 120
        varying vec2 v_texcoord;
        uniform sampler2D texture;
        void main() {
            gl_FragColor = texture2D(texture, v_texcoord);
        }
        """

        shader = shaders.compileProgram(
            shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        )

        vertices = np.array([
            -0.5, -0.5, 0.0, 0.0,
            0.5, -0.5, 1.0, 0.0,
            0.5, 0.5, 1.0, 1.0,
            -0.5, 0.5, 0.0, 1.0
        ], dtype=np.float32)

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        position = glGetAttribLocation(shader, "position")
        texcoord = glGetAttribLocation(shader, "texcoord")
        glEnableVertexAttribArray(position)
        glEnableVertexAttribArray(texcoord)
        glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 16, None)
        glVertexAttribPointer(texcoord, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))

        self.last_time = glfw.get_time()

        while not glfw.window_should_close(self.window):
            current_time = glfw.get_time()
            dt = current_time - self.last_time
            self.last_time = current_time

            self.process_input(dt)

            for entity in self.entities:
                entity.update(dt)

            for i in range(len(self.entities)):
                for j in range(i + 1, len(self.entities)):
                    if self.check_collision(self.entities[i], self.entities[j]):
                        self.handle_collision(self.entities[i], self.entities[j])

            glClear(GL_COLOR_BUFFER_BIT)

            glUseProgram(shader)

            for entity in self.entities:
                glBindTexture(GL_TEXTURE_2D, entity.texture)
                translation_location = glGetUniformLocation(shader, "translation")
                scale_location = glGetUniformLocation(shader, "scale")
                glUniform2f(translation_location, *entity.position)
                glUniform2f(scale_location, *entity.size)
                glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glfw.terminate()


if __name__ == "__main__":
    game = Game(1200, 1000)

    game.init_glfw()

    # Add entities
    game.add_entity("assets/fongk.png",
                    "User",
                    (0.0, 0.0),
                    is_user=True)
    game.add_entity("assets/RedCube.png", "Static1", (0.5, 0.5))
    game.add_entity("assets/YellowCube.png", "Static2", (-0.5, -0.5))

    game.run()
