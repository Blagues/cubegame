import moderngl
import numpy as np
import glfw
from OpenGL.GL import *
import freetype


class Square:
    def __init__(self):
        self.size = 0.05
        self.mass = 1.0

        self.position = np.array([0.0, 0.0], dtype=np.float32)  # Start near the bottom
        self.velocity = np.array([0.0, 0.0], dtype=np.float32)
        self.acceleration = np.array([0.0, -9.81], dtype=np.float32)  # Gravity
        self.max_velocity = np.array([10.0, 50.0], dtype=np.float32)
        self.drag = np.array([0.9, 1], dtype=np.float32)

        self.on_ground = False

    def apply_force(self, force):
        self.acceleration += force / self.mass

    def jump(self):
        if self.on_ground:
            self.velocity[1] = 2.5  # Jump velocity
            self.on_ground = False

    def update(self, dt):
        self.velocity *= self.drag
        self.velocity += self.acceleration * dt
        self.velocity = np.clip(self.velocity, -self.max_velocity, self.max_velocity)

        new_position = self.position + self.velocity * dt

        self.on_ground = False  # Reset ground check

        # Constrain position within bounds and handle bouncing
        for i in range(2):
            if new_position[i] < -1 + self.size or new_position[i] > 1 - self.size:

                if i == 1 and new_position[i] <= -1 + self.size:  # Check if on ground
                    self.on_ground = True
                    self.velocity[i] *= 0  # Bounce with some energy loss
                else:
                    self.velocity[i] *= -0.8  # Bounce with more energy loss

                new_position[i] = np.clip(new_position[i], -1 + self.size, 1 - self.size)

        self.position = new_position
        self.acceleration = np.array([0.0, -9.8], dtype=np.float32)  # Reset acceleration, keeping gravity


class TextRenderer:
    def __init__(self, ctx, width, height):
        self.ctx = ctx
        self.width = width
        self.height = height

        self.prog = self.ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            ''',
            fragment_shader='''
                #version 330
                uniform sampler2D Texture;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    f_color = vec4(1.0, 1.0, 1.0, texture(Texture, v_texcoord).r);
                }
            '''
        )

        self.face = freetype.Face("fonts/PlayfairDisplay-Bold.ttf")
        self.face.set_char_size(48 * 64)

    def render_text(self, text, x, y):
        x_pos = x
        for c in text:
            self.face.load_char(c)
            glyph = self.face.glyph

            # Convert the bitmap buffer to bytes
            buffer = bytes(glyph.bitmap.buffer)

            texture = self.ctx.texture((glyph.bitmap.width, glyph.bitmap.rows), 1, buffer)
            texture.use()

            x2 = x_pos + glyph.bitmap_left
            y2 = -y - glyph.bitmap_top
            w = glyph.bitmap.width
            h = glyph.bitmap.rows

            x_pos += (glyph.advance.x >> 6)

            vertices = np.array([
                x2, -y2, 0, 0,
                x2 + w, -y2, 1, 0,
                x2, -y2 - h, 0, 1,
                x2 + w, -y2 - h, 1, 1,
            ], dtype=np.float32)

            vbo = self.ctx.buffer(vertices.tobytes())
            vao = self.ctx.vertex_array(self.prog, [(vbo, '2f 2f', 'in_vert', 'in_texcoord')])
            vao.render(moderngl.TRIANGLE_STRIP)


class SquareApp:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.square = Square()
        self.last_time = 0
        self.frame_count = 0
        self.last_fps_update = 0
        self.fps = 0

    def init_glfw(self):
        if not glfw.init():
            raise Exception("GLFW cannot be initialized")

        self.window = glfw.create_window(self.width, self.height, "ModernGL 2D Square", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window cannot be created")

        glfw.set_window_pos(self.window, 100, 100)
        glfw.make_context_current(self.window)

    def process_input(self):
        if glfw.get_key(self.window, glfw.KEY_ESCAPE) == glfw.PRESS:
            glfw.set_window_should_close(self.window, True)

        move_force = 5.0
        if glfw.get_key(self.window, glfw.KEY_LEFT) == glfw.PRESS:
            self.square.apply_force(np.array([-move_force, 0]))
        if glfw.get_key(self.window, glfw.KEY_RIGHT) == glfw.PRESS:
            self.square.apply_force(np.array([move_force, 0]))
        if glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS:
            self.square.jump()

    def run(self):
        self.init_glfw()
        ctx = moderngl.create_context()

        prog = ctx.program(
            vertex_shader='''
                #version 330
                in vec2 in_position;
                uniform vec2 translation;
                void main() {
                    gl_Position = vec4(in_position + translation, 0.0, 1.0);
                }
            ''',
            fragment_shader='''
                #version 330
                uniform sampler2D Texture;
                in vec2 v_texcoord;
                out vec4 f_color;
                void main() {
                    float alpha = texture(Texture, v_texcoord).r;
                    f_color = vec4(1.0, 0.0, 0.0, alpha);  // Red text for visibility
                }
            '''
        )
        # use square size in vertex shader
        vertices = np.array([
            self.square.size, -self.square.size,
            self.square.size, self.square.size,
            -self.square.size, self.square.size,
            -self.square.size, -self.square.size
        ], dtype='f4')

        indices = np.array([0, 1, 2, 2, 3, 0], dtype='i4')

        vbo = ctx.buffer(vertices.tobytes())
        ibo = ctx.buffer(indices.tobytes())

        vao = ctx.vertex_array(prog, [(vbo, '2f', 'in_position')], ibo)

        translation_uniform = prog['translation']

        text_renderer = TextRenderer(ctx, self.width, self.height)

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

                print(f"FPS: {self.fps}")

            self.process_input()
            self.square.update(dt)

            ctx.clear(0.15, 0.15, 0.15)

            translation_uniform.value = tuple(self.square.position)

            vao.render()

            # Render FPS text
            text_renderer.render_text(f"FPS: {self.fps}", -0.7, 0.7)

            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glfw.terminate()


if __name__ == "__main__":
    app = SquareApp(1200, 1000)
    app.run()
