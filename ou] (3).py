from ursina import *
from math import sin, cos, radians
import random, time as systime

app = Ursina()

# ===== Window Setup =====
window.title = '🚗 yuvraj 3d parking game!'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = True
window.fps_counter.enabled = True

# ===== Colours =====
GROUND_COLOR = color.gray
PARKING_COLOR = color.green.tint(-0.2)
CAR_COLOR = color.red
OBSTACLE_COLOR = color.yellow.tint(0.3)
TEXT_COLOR = color.lime
SPEED_TEXT_COLOR = color.red

# ===== Sky =====
Sky(texture='sky_sunset')  # or Sky() for default blue sky

# ===== Lighting =====
sun = DirectionalLight(shadows=True, rotation=(45, -45, 0))
sun.color = color.white
AmbientLight(color=color.rgba(180, 180, 200, 0.6))

# ===== Boundaries =====
boundary_thickness = 1
boundary_height = 3
boundary_length = 100
boundary_width = 30

# Front boundary
Entity(model='cube', scale=(boundary_width, boundary_height, boundary_thickness), position=(0, boundary_height/2, boundary_length/2), collider='box', color=color.clear)
# Back boundary
Entity(model='cube', scale=(boundary_width, boundary_height, boundary_thickness), position=(0, boundary_height/2, -boundary_length/2), collider='box', color=color.clear)
# Left boundary
Entity(model='cube', scale=(boundary_thickness, boundary_height, boundary_length), position=(-boundary_width/2, boundary_height/2, 0), collider='box', color=color.clear)
# Right boundary
Entity(model='cube', scale=(boundary_thickness, boundary_height, boundary_length), position=(boundary_width/2, boundary_height/2, 0), collider='box', color=color.clear)

# ===== Ground =====
ground = Entity(model='plane', scale=(boundary_width, 1, boundary_length), texture='white_cube', texture_scale=(boundary_width, boundary_length), color=GROUND_COLOR, collider='box')

# ===== UI =====
message = Text('', origin=(0,0), scale=2, y=0.4, color=TEXT_COLOR, background=True)
speed_text = Text('Speed: 0', position=window.top_left + Vec2(0.1,-0.1), scale=1.5, color=SPEED_TEXT_COLOR)
timer_text = Text('Time: 0.0', position=window.top_left + Vec2(0.1,-0.2), scale=1.5, color=color.azure)
best_time_text = Text('Best: --', position=window.top_left + Vec2(0.1,-0.3), scale=1.5, color=color.yellow)
mode_text = Text('Mode: Car (Cam: Locked-Fixed)', position=window.top_left + Vec2(0.1,-0.4), scale=1.2, color=color.cyan)
zoom_text = Text('Zoom: 0', position=window.top_left + Vec2(0.1,-0.5), scale=1.2, color=color.pink)
controls_text = Text(
    text=(
        "Controls:\n"
        " W/S = Forward/Back | A/D = Steer | B = Brake\n"
        " Camera: V = Toggle Cam | scroll down/scroll up = Zoom\n"
        " Misc: R = Reset"
    ),
    position=window.bottom_left + Vec2(0.1,0.1),
    origin=(-0.5,-0.5),
    scale=1,
    color=color.white,
    background=False
)

# ===== Car Class =====
class Car(Entity):
    def __init__(self):
        super().__init__()
        self.model = 'cube'
        self.color = CAR_COLOR
        self.scale = (2, 0.5, 4)
        self.position = (0, 0.25, -45)
        self.collider = 'box'
        self.speed = 0
        self.velocity = Vec3(0,0,0)
        self.rotation_y = 0
        self.max_speed = 10
        self.acceleration = 10
        self.deceleration = 8
        self.steering = 40
        self.brake_force = 20

    def reset(self):
        self.position = (0, 0.25, -45)
        self.rotation_y = 0
        self.speed = 0
        self.velocity = Vec3(0,0,0)

    def update_move(self, dt, obstacles):
        forward = held_keys['w']
        backward = held_keys['s']
        left = held_keys['a']
        right = held_keys['d']
        brake = held_keys['b']

        if forward:
            self.speed += self.acceleration * dt
        elif backward:
            self.speed -= self.acceleration * dt
        else:
            if self.speed > 0:
                self.speed -= self.deceleration * dt
            elif self.speed < 0:
                self.speed += self.deceleration * dt

        if brake:
            if self.speed > 0:
                self.speed -= self.brake_force * dt
            elif self.speed < 0:
                self.speed += self.brake_force * dt

        self.speed = clamp(self.speed, -self.max_speed/2, self.max_speed)

        if abs(self.speed) > 0.1:
            if left:
                self.rotation_y += self.steering * dt * (self.speed / self.max_speed)
            if right:
                self.rotation_y -= self.steering * dt * (self.speed / self.max_speed)

        rad = radians(self.rotation_y)
        self.velocity = Vec3(sin(rad), 0, cos(rad)) * self.speed
        self.position += self.velocity * dt

        for o in obstacles:
            if self.intersects(o).hit:
                self.speed = 0
                return True

        if abs(self.position.x) > boundary_width/2 - 1 or abs(self.position.z) > boundary_length/2 - 1:
            self.speed = 0
            return True

        return False

    def update_camera(self, dt, camera_mode, zoom):
        camera_distance = 10 + zoom
        camera_height = 5 + zoom * 0.5
        camera_position = self.position + Vec3(0, camera_height, -camera_distance)
        camera.position = camera_position
        camera.look_at(self.position + Vec3(0,1,0))

# ===== GameManager =====
class GameManager:
    def __init__(self):
        self.car = Car()

        self.parking_spot = Entity(model='plane', scale=(3,1,4), color=PARKING_COLOR, position=(0,0,45))
        self.parking_box = Entity(model='cube', scale=(2.8,0.5,3.8), position=(0,0.25,45), collider='box', visible=False)

        self.obstacles = []
        for z in range(-25, 40, 8):
            for _ in range(2):
                x_pos = random.choice([-4, -2, 0, 2, 4])
                self.obstacles.append(Entity(model='cube', color=OBSTACLE_COLOR, scale=(1,1,1), position=(x_pos, 0.5, z), collider='box'))

        self.camera_mode = 'locked_fixed'
        self.start_time = None
        self.best_time = None
        self.zoom = 0
        self.game_running = False

    def reset(self):
        message.text = ''
        self.start_time = systime.time()
        self.car.reset()
        self.parking_spot.color = PARKING_COLOR
        self.game_running = True

    def update(self, dt):
        if not self.game_running:
            return

        crashed = self.car.update_move(dt, self.obstacles)
        self.car.update_camera(dt, self.camera_mode, self.zoom)
        speed_text.text = f"Speed: {round(abs(self.car.speed),1)}"
        mode_text.text = f"Mode: Car (Cam: {self.camera_mode.replace('_','-')})"
        zoom_text.text = f"Zoom: {self.zoom}"
        elapsed = systime.time() - self.start_time if self.start_time else 0
        timer_text.text = f"Time: {elapsed:.1f}"

        if crashed:
            message.text = "Crashed! Press R to Reset"
        else:
            message.text = ''

        if distance(self.car.position, self.parking_spot.position) < 2:
            message.text = f"Car Parked! Time: {elapsed:.1f}"
            if self.best_time is None or elapsed < self.best_time:
                self.best_time = elapsed
            best_time_text.text = f"Best: {self.best_time:.1f}"
            self.game_running = False

game_manager = GameManager()

# ===== Utility =====
def distance(a, b):
    return (a - b).length()

# ===== Input Handling =====
def input(key):
    if not app.game_started:
        return

    if key == 'r':
        game_manager.reset()
    if key == 'v':
        modes = ['locked_fixed', 'locked_follow', 'chase', 'cinematic']
        idx = modes.index(game_manager.camera_mode)
        game_manager.camera_mode = modes[(idx+1) % len(modes)]
    if key == 'scroll up':
        game_manager.zoom = clamp(game_manager.zoom - 1, -10, 20)
    if key == 'scroll down':
        game_manager.zoom = clamp(game_manager.zoom + 1, -10, 20)

# ===== Global update function =====
def update():
    if hasattr(app, 'game_started') and app.game_started:
        game_manager.update(time.dt)

# ===== Welcome UI =====
def start_game():
    app.game_started = True
    start_button.visible = False
    welcome_text.visible = False
    game_manager.reset()

welcome_text = Text("Welcome to yuvraj 3d parking game!\nClick Start to begin.", origin=(0,0), scale=2, y=0.2, color=color.azure)
start_button = Button(text='Start Game', color=color.green.tint(-0.2), scale=(0.2,0.1), y=-0.1)
start_button.on_click = start_game

app.game_started = False

app.run()
