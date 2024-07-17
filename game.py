import glfw
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy as np

from movable_entity import MovableEntity


class SquareApp:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.user_square = MovableEntity("UserSquare", 1, 0.1,
                                         np.array([0.0, 0.0], dtype=np.float32),
                                         max_velocity=np.array([15, 15]),
                                         drag=np.array([0.85, 0.85]))
        self.static_square = MovableEntity("StaticSquare", 2, 0.1,
                                           np.array([0.5, 0.5], dtype=np.float32),
                                           max_velocity=np.array([0, 0]),
                                           drag=np.array([1, 1]))
        self.last_time = 0
        self.frame_count = 0
        self.last_fps_update = 0
        self.fps = 0

    def init_glfw(self):
        if not glfw.init():
            raise Exception("GLFW cannot be initialized")

        self.window = glfw.create_window(self.width, self.height, "GLFW OpenGL Square", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window cannot be created")

        glfw.set_window_pos(self.window, 100, 100)
        glfw.make_context_current(self.window)

    def process_input(self, dt):
        if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(self.window, True)

        move_force = 20
        if glfw.get_key(self.window, glfw.KEY_LEFT) == glfw.PRESS:
            self.user_square.add_velocity(np.array([-move_force, 0]), dt)
        if glfw.get_key(self.window, glfw.KEY_RIGHT) == glfw.PRESS:
            self.user_square.add_velocity(np.array([move_force, 0]), dt)
        if glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS:
            self.user_square.add_velocity(np.array([0, move_force]), dt)
        if glfw.get_key(self.window, glfw.KEY_DOWN) == glfw.PRESS:
            self.user_square.add_velocity(np.array([0, -move_force]), dt)

    def check_collision(self, square1, square2):
        return (abs(square1.position[0] - square2.position[0]) < (square1.size + square2.size) and
                abs(square1.position[1] - square2.position[1]) < (square1.size + square2.size))

    def handle_collision(self, square1, square2):
        overlap_x = (square1.size + square2.size) - abs(square1.position[0] - square2.position[0])
        overlap_y = (square1.size + square2.size) - abs(square1.position[1] - square2.position[1])

        if overlap_x < overlap_y:
            if square1.position[0] < square2.position[0]:
                square1.position[0] -= overlap_x / 2
                square2.position[0] += overlap_x / 2
            else:
                square1.position[0] += overlap_x / 2
                square2.position[0] -= overlap_x / 2

        else:
            if square1.position[1] < square2.position[1]:
                square1.position[1] -= overlap_y / 2
                square2.position[1] += overlap_y / 2
            else:
                square1.position[1] += overlap_y / 2
                square2.position[1] -= overlap_y / 2
    def run(self):
        self.init_glfw()

        vertex_shader = """
        #version 120
        attribute vec2 position;
        uniform vec2 translation;
        void main() {
            gl_Position = vec4(position + translation, 0.0, 1.0);
        }
        """

        fragment_shader = """
        #version 120
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }
        """

        shader = shaders.compileProgram(
            shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER)
        )

        vertices = np.array([
            self.user_square.size, -self.user_square.size,
            self.user_square.size, self.user_square.size,
            -self.user_square.size, self.user_square.size,
            -self.user_square.size, -self.user_square.size
        ], dtype=np.float32)

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        position = glGetAttribLocation(shader, "position")
        glEnableVertexAttribArray(position)
        glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 0, None)

        self.last_time = glfw.get_time()

        while not glfw.window_should_close(self.window):
            current_time = glfw.get_time()
            dt = current_time - self.last_time
            self.last_time = current_time

            self.frame_count += 1
            if current_time - self.last_fps_update >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_fps_update = current_time

            self.process_input(dt)
            self.user_square.update(dt)
            self.static_square.update(dt)

            if self.check_collision(self.user_square, self.static_square):
                self.handle_collision(self.user_square, self.static_square)

            glClear(GL_COLOR_BUFFER_BIT)

            glUseProgram(shader)

            # Draw user square
            translation_location = glGetUniformLocation(shader, "translation")
            glUniform2f(translation_location, *self.user_square.position)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glEnableVertexAttribArray(position)
            glVertexAttribPointer(position, 2, GL_FLOAT, GL_FALSE, 0, None)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

            # Draw static square
            glUniform2f(translation_location, *self.static_square.position)
            glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

            glDisableVertexAttribArray(position)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glfw.terminate()


if __name__ == "__main__":
    app = SquareApp(1200, 1000)
    app.run()