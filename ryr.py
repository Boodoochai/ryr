import sys
import time
import math
from sys import stdout
from multiprocessing import Pool


class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        return Vector3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        return Vector3(self.x / other, self.y / other, self.z / other)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalized(self):
        return self / self.length()

    def get_distance(self, point):
        return math.sqrt((self.x - point.x) ** 2 + (self.y - point.y) ** 2 + (self.z - point.z) ** 2)

    def dot_product(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z


class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        return Vector2(self.x / other, self.y / other)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self):
        return self / self.length()


class Ray:
    def __init__(self, position, direction):
        self.position = position
        self.direction = direction

    @staticmethod
    def ray_from_points(start: Vector3, to: Vector3):
        return Ray(start, (to - start).normalized())


class Settings:
    space = ' '
    screen_width = 232
    screen_height = 63
    fps = 60
    screen_size = Vector2(1, 9 / 16)
    screen_distance = 1
    walls = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'."


class Screen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # self.data = [[0] * width for _ in range(height)]


class Camera:
    def __init__(self, position, direction):
        self.screen = Screen(Settings.screen_width, Settings.screen_height)
        self.position = position
        self.direction = direction
        self.screen_size = Settings.screen_size
        self.screen_dist = Settings.screen_distance

    def get_screen_point_cords(self, x, y):
        point = self.position + self.direction.normalized() * self.screen_dist
        point += Vector3(-1, 0, 0) * self.screen_size.x / 2
        point += Vector3(0, 0, 1) * self.screen_size.y / 2
        point += Vector3(1, 0, 0) * self.screen_size.x * x / Settings.screen_width
        point += Vector3(0, 0, -1) * self.screen_size.y * y / Settings.screen_height
        return point


class Torus:
    def __init__(self, position, direction, minor_radius, major_radius):
        self.position = position
        self.direction = direction
        self.minor_radius = minor_radius
        self.major_radius = major_radius

    def get_distance(self, point: Vector3):
        ao = self.position - point
        ah = self.direction * ao.dot_product(self.direction)
        ho = ao - ah
        ho1 = ho * (1 - self.major_radius / ho.length())
        ao1 = ah + ho1
        ax = ao1 * (1 - self.minor_radius / ao1.length())
        return ax.length()


class Sphere:
    def __init__(self, position, radius):
        self.position = position
        self.radius = radius

    def get_distance(self, point):
        return self.position.get_distance(point) - self.radius


class Scene:
    def __init__(self, camera):
        self.camera = camera
        self.objects = []

    def add_object(self, object):
        self.objects.append(object)


class Renderer:
    def render_part(self, *args):
        scene, start_y, end_y = args[0]

        print(start_y, end_y)

        get_cords = scene.camera.get_screen_point_cords
        pos = scene.camera.position
        width, height = scene.camera.screen.width, scene.camera.screen.height

        data = [[0] * width for _ in range(end_y - start_y)]

        for x in range(width):
            for y in range(start_y, end_y):
                point = get_cords(x, y)
                ray = Ray.ray_from_points(pos, point)

                k = 0
                while True:
                    k += 1
                    min_dist = 99999999999999999999999999999999999
                    for obj in scene.objects:
                        min_dist = min(min_dist, obj.get_distance(ray.position))
                    ray.position = ray.position + ray.direction.normalized() * min_dist
                    if min_dist < 0.01:
                        dist = pos.get_distance(ray.position)
                        data[y - start_y][x] = Settings.walls[int(min(dist, 30) / 30 * len(Settings.walls))]
                        break
                    if k > 10:
                        data[y - start_y][x] = Settings.space
                        break

        return data

    def render(self, scene: Scene):
        # print("Prerender")
        screen_part = Settings.screen_height // 4
        future = Game.pool.map_async(
            self.render_part, [(scene, screen_part * i, screen_part * (i + 1)) for i in range(4)])
        data = future.get()

        # Game.pool.join()

        # print("Calculated")

        for part in data:
            # print(part)
            for line in part:
                stdout.write(''.join(line) + '\n')
        stdout.flush()

        # print("Postrender")


class Game:
    pool = Pool(processes=4)

    def __init__(self):
        self.renderer = Renderer()
        camera = Camera(Vector3(0, 0, 0), Vector3(0, 1, 0))
        self.scene = Scene(camera)

        torus1 = Torus(Vector3(0, 20, 0.0000001), Vector3(0, 1, 0).normalized(), 1, 4)
        self.scene.add_object(torus1)

        # self.scene.add_sphere(Vector3(0, 9, 0), 2)
        # self.scene.add_sphere(Vector3(4, 7, 0), 2)

    def run(self):
        time_on_frame = 1 / Settings.fps

        while True:
            self.update()

            self.draw()

            # time.sleep(time_on_frame)

    x = 0

    def update(self):
        self.x += 10
        if self.x == 360:
            self.x = 0
        self.scene.objects[0].direction = Vector3(math.cos(self.x / 180 * math.pi), math.sin(self.x / 180 * math.pi),
                                                  0).normalized()

    def draw(self):
        self.renderer.render(self.scene)
        # print("render done")


def main():
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
