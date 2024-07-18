import time
import glfw
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np
from PIL import Image
import ctypes
import uuid
from threading import Lock

from movable_entity import MovableEntity
from network_manager import NetworkManager


class Game:
    def __init__(self, width, height, host='127.0.0.1', port=5000):
        self.width = width
        self.height = height
        self.entities = {}
        self.user_entity = None
        self.last_time = 0
        self.texture_cache = {}
        self.texture_cache_lock = Lock()
        self.texture_loading_queue = []

        self.network = NetworkManager(host, port, self)
        self.network.start()

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
        with self.texture_cache_lock:
            if file_path in self.texture_cache:
                return self.texture_cache[file_path]

        try:
            image = Image.open(file_path).convert("RGBA")
        except IOError:
            print(f"Error: Unable to open the image file: {file_path}")
            return None

        print(f"Loaded image: {file_path}")

        image_data = image.tobytes()
        width, height = image.size

        print(f"Image size: {width}x{height}")

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        self.check_gl_error("glTexImage2D")

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        self.check_gl_error("glTexParameteri MIN_FILTER")
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        self.check_gl_error("glTexParameteri MAG_FILTER")

        with self.texture_cache_lock:
            self.texture_cache[file_path] = (texture, (width, height))

        return texture, (width, height)

    def check_gl_error(self, operation):
        error = glGetError()
        if error != GL_NO_ERROR:
            print(f"OpenGL error after {operation}: {error}")

    def add_entity(self, file_path, name, position, max_velocity=np.array([15, 15]), drag=(0.9, 0.9), is_user=False,
                   network_id=None):
        print(f"Adding entity: {name}")

        if not isinstance(position, np.ndarray):
            position = np.array(position, dtype=np.float32)
        if not isinstance(max_velocity, np.ndarray):
            max_velocity = np.array(max_velocity, dtype=np.float32)
        if not isinstance(drag, np.ndarray):
            drag = np.array(drag, dtype=np.float32)

        id = network_id if network_id else (uuid.uuid1().int % 1000000 + int(time.time()))

        # Use a default size when creating the entity
        default_size = np.array([0.1, 0.1], dtype=np.float32)
        entity = MovableEntity(name, None, id, default_size, position, max_velocity, drag)

        if is_user:
            self.user_entity = entity
        else:
            self.entities[id] = entity

        self.schedule_texture_loading(entity, file_path)

        print(f"Added entity: {entity}")

    def schedule_texture_loading(self, entity, file_path):
        def load_texture_for_entity():
            texture_info = self.load_texture(file_path)
            if texture_info is None:
                print(f"Failed to load texture for entity: {entity.name}")
                return

            texture, (width, height) = texture_info
            size = np.array([width / self.width * 4, height / self.height * 4],
                            dtype=np.float32)  # Normalize and scale up

            entity.texture = texture
            entity.size = size

        self.texture_loading_queue.append(load_texture_for_entity)

    def process_input(self, dt, update_time):
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

            # only update if velocity is greater than 0, and we haven't updated in the last 0.01 seconds
            if np.linalg.norm(self.user_entity.velocity) > 0 and update_time > 0.01:
                self.network.send_data({
                    "type": "update",
                    "network_id": self.user_entity.id,
                    "position": [float(x) for x in self.user_entity.position]
                })

                return True

        return False

    def handle_network_data(self, data):
        print(f"Received data: {data}")
        if data["type"] == "update":
            net_id = data["network_id"]

            if net_id in self.entities.keys():
                print(f"Updating entity with network id: {net_id}")
                self.entities[net_id].position = np.array(data["position"], dtype=np.float32)
            else:
                print(f"Creating new entity with network id: {net_id}")
                self.add_entity("assets/BlueCube.png",
                                f"OtherUser_{data['network_id']}",
                                data["position"],
                                network_id=data["network_id"])

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
        update_time = 0

        while not glfw.window_should_close(self.window):
            current_time = glfw.get_time()
            dt = current_time - self.last_time
            self.last_time = current_time

            if self.process_input(dt, update_time):
                update_time = 0
            else:
                update_time += dt

            self.user_entity.update(dt)

            for load_texture in self.texture_loading_queue:
                load_texture()
            self.texture_loading_queue.clear()

            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(shader)
            self.draw_entities(shader, [entity for entity in self.entities.values() if entity.texture is not None] +
                               ([
                                    self.user_entity] if self.user_entity and self.user_entity.texture is not None else []))

            glfw.swap_buffers(self.window)
            glfw.poll_events()

        self.network.close()
        glfw.terminate()

    def draw_entities(self, shader, entities):
        for entity in entities:
            if entity.texture is None:
                continue
            glBindTexture(GL_TEXTURE_2D, entity.texture)
            translation_location = glGetUniformLocation(shader, "translation")
            scale_location = glGetUniformLocation(shader, "scale")
            glUniform2f(translation_location, *entity.position)
            glUniform2f(scale_location, *entity.size)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
            self.check_gl_error("glDrawArrays")


if __name__ == "__main__":
    game = Game(1200, 1000)
    game.init_glfw()
    game.add_entity("assets/RedCube.png", "User", (0.5, 0.5), is_user=True)
    game.run()
