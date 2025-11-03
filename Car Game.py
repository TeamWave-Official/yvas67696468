from ursina import *
from math import sin, cos, radians
import random, os, time as systime

app = Ursina()

# ===== Window Setup =====
window.title = '🚗 Banana Car & ✈ Plane Parking Game!'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = True
window.fps_counter.enabled = True

# ===== Colours =====
GROUND_COLOR = color.gray
PARKING_COLOR = color.green.tint(-0.2)
CAR_COLOR = color.red
WHEEL_COLOR = color.black
OBSTACLE_COLOR = color.azure.tint(0.3)
TEXT_COLOR = color.lime
SPEED_TEXT_COLOR = color.orange

# ===== Lighting =====
DirectionalLight(y=3, z=5, shadows=True, rotation=(45, -30, 0))
AmbientLight(color=color.rgba(100, 100, 120, 0.4))

# ===== Entities =====
ground = Entity(model='plane', scale=(30,1,100), texture='white_cube',
                texture_scale=(30,100), color=GROUND_COLOR, collider='box')

# 🚧 Barriers on edges 🚧
barriers = []
barrier_thickness = 1
barrier_height = 3
barrier_z_length = 100
barrier_x_length = 30

# Left & Right
barriers.append(Entity(model='cube', color=color.clear, scale=(barrier_thickness, barrier_height, barrier_z_length),
                       position=(-barrier_x_length/2, barrier_height/2, 0), collider='box', visible=False))
barriers.append(Entity(model='cube', color=color.clear, scale=(barrier_thickness, barrier_height, barrier_z_length),
                       position=(barrier_x_length/2, barrier_height/2, 0), collider='box', visible=False))

# Front only (no back!)
barriers.append(Entity(model='cube', color=color.clear, scale=(barrier_x_length, barrier_height, barrier_thickness),
                       position=(0, barrier_height/2, barrier_z_length/2), collider='box', visible=False))

# ===== UI =====
message = Text('', origin=(0,0), scale=2, y=0.4, color=TEXT_COLOR, background=True)
speed_text = Text('Speed: 0', position=window.top_left + Vec2(0.1,-0.1),
                  scale=1.5, color=SPEED_TEXT_COLOR)
timer_text = Text('Time: 0.0', position=window.top_left + Vec2(0.1,-0.2),
                  scale=1.5, color=color.azure)
best_time_text = Text('Best: --', position=window.top_left + Vec2(0.1,-0.3),
                      scale=1.5, color=color.yellow)
mode_text = Text('Mode: Car (Cam: Locked)', position=window.top_left + Vec2(0.1,-0.4),
                 scale=1.2, color=color.cyan)
zoom_text = Text('Zoom: 0', position=window.top_left + Vec2(0.1,-0.5),
                 scale=1.2, color=color.pink)

controls_text = Text(
    text=(
        "Controls:\n"
        " Car: W/S = Forward/Back | A/D = Steer | B = Brake\n"
        " Plane: ↑/↓ = Throttle | W/S = Pitch | A/D = Yaw\n"
        " Camera: V = Toggle Cam | Q/E = Zoom\n"
        " Misc: C = Switch Mode | R = Reset"
    ),
    position=window.bottom_left + Vec2(0.1,0.1),
    origin=(-0.5,-0.5),
    scale=1,
    color=color.white
)

# ===== Classes =====
class Car(Entity):
    def __init__(self):
        super().__init__(model='cube', color=CAR_COLOR, scale=(1,0.5,2),
                         position=(0,0.25,-45), collider='box')
        for offset in [(-0.5,-0.25,0.8),(0.5,-0.25,0.8),
                       (-0.5,-0.25,-0.8),(0.5,-0.25,-0.8)]:
            Entity(parent=self, model='sphere', color=WHEEL_COLOR,
                   scale=0.2, position=offset)
        self.velocity = Vec3(0,0,0)
        self.target_rotation = 0
        self.rotation_velocity = 0
        # settings
        self.accel, self.rev_accel = 4, 2
        self.max_speed, self.max_rev = 9, 4.5
        self.friction, self.rot_speed = 6, 60

    def reset(self):
        self.position = Vec3(0,0.25,-45)
        self.rotation_y = 0
        self.velocity = Vec3(0,0,0)
        self.target_rotation = 0
        self.rotation_velocity = 0

    def update_move(self, dt, obstacles):
        move_input = held_keys['w'] - held_keys['s']
        angle_rad = radians(self.rotation_y)
        forward = Vec3(sin(angle_rad),0,cos(angle_rad)).normalized()

        steer_input = held_keys['d'] - held_keys['a']
        steering_eff = min(self.velocity.length()/self.max_speed, 1)
        self.rotation_velocity += steer_input * self.rot_speed * steering_eff * dt
        self.rotation_velocity -= self.rotation_velocity * 3 * dt
        self.target_rotation += self.rotation_velocity * dt
        self.rotation_y = lerp_angle(self.rotation_y, self.target_rotation, 8*dt)

        if move_input == 1:
            self.velocity += forward * self.accel * dt
        elif move_input == -1:
            self.velocity += forward * -self.rev_accel * dt
        else:
            self.velocity -= self.velocity * min(self.friction*dt,1)

        if held_keys['b']:
            self.velocity -= self.velocity * min(12*dt,1)

        if self.velocity.length() > self.max_speed and move_input == 1:
            self.velocity = self.velocity.normalized() * self.max_speed
        if self.velocity.length() > self.max_rev and move_input == -1:
            self.velocity = self.velocity.normalized() * self.max_rev

        self.velocity.y -= 9.8*dt
        self.position += self.velocity*dt
        if self.y < 0.25:
            self.y = 0.25
            self.velocity.y = 0

        hit = self.intersects()
        if hit.hit and hit.entity in obstacles:
            return True
        if hit.hit and hit.entity in barriers:
            return True
        return False

    def update_camera(self, dt, mode, zoom):
        angle_rad = radians(self.rotation_y)
        forward = Vec3(sin(angle_rad),0,cos(angle_rad)).normalized()

        if mode == 'locked':
            cam_pos = self.position - forward*(8+zoom) + Vec3(0,4+zoom*0.5,0)
            camera.position = cam_pos
            camera.rotation = (20, self.rotation_y, 0)

        elif mode == 'chase':
            cam_target = self.position - forward*(8+zoom) + Vec3(0,4+zoom*0.5,0)
            camera.position = lerp(camera.position, cam_target, 5*dt)
            camera.rotation = (20, self.rotation_y, 0)

        elif mode == 'cinematic':
            t = systime.time()
            orbit_radius = 10 + zoom + sin(t*0.7)*2
            orbit_speed = 0.25 + 0.05*sin(t*0.3)
            cam_x = self.x + orbit_radius * cos(t*orbit_speed)
            cam_z = self.z + orbit_radius * sin(t*orbit_speed)
            cam_y = self.y + 6 + sin(t*0.6)*3
            camera.position = lerp(camera.position, Vec3(cam_x, cam_y, cam_z), 2*dt)
            camera.look_at(self.position + Vec3(0,1,0))

class Plane(Entity):
    def __init__(self):
        super().__init__(model='cube', color=color.white, scale=(1,0.3,3),
                         position=(0,5,-45), collider='box', visible=False)
        Entity(parent=self, model='cube', color=color.white, scale=(6,0.1,0.3),
               position=(0,0,0))
        Entity(parent=self, model='cube', color=color.white, scale=(1.5,0.1,0.8),
               position=(0,0,-1.2))
        self.velocity = Vec3(0,0,0)
        self.accel, self.max_speed, self.friction = 5, 15, 1.5

    def reset(self):
        self.position = Vec3(0,5,-45)
        self.rotation = Vec3(0,0,0)
        self.velocity = Vec3(0,0,0)

    def update_move(self, dt, obstacles):
        move_input = held_keys['up arrow'] - held_keys['down arrow']
        forward = self.forward
        if move_input != 0:
            self.velocity += forward * self.accel * move_input * dt
        else:
            self.velocity -= self.velocity * min(self.friction*dt,1)
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalized() * self.max_speed

        self.rotation_x += (held_keys['w']-held_keys['s'])*30*dt
        self.rotation_y += (held_keys['a']-held_keys['d'])*30*dt

        self.position += self.velocity*dt

        for ob in obstacles + barriers:
            if self.intersects(ob).hit:
                return True
        return False

    def update_camera(self, dt, mode, zoom):
        if mode == 'locked':
            cam_pos = self.position + Vec3(0,5+zoom*0.5,-15-zoom)
            camera.position = cam_pos
            camera.rotation = (20, 0, 0)

        elif mode == 'chase':
            cam_target = self.position + Vec3(0,5+zoom*0.5,-15-zoom)
            camera.position = lerp(camera.position, cam_target, 5*dt)
            camera.rotation = (20, 0, 0)

        elif mode == 'cinematic':
            t = systime.time()
            orbit_radius = 18 + zoom + cos(t*0.8)*3
            orbit_speed = 0.2 + 0.05*cos(t*0.4)
            cam_x = self.x + orbit_radius * cos(t*orbit_speed)
            cam_z = self.z + orbit_radius * sin(t*orbit_speed)
            cam_y = self.y + 8 + cos(t*0.5)*4
            camera.position = lerp(camera.position, Vec3(cam_x, cam_y, cam_z), 2*dt)
            camera.look_at(self.position + Vec3(0,1,0))

# ===== GameManager =====
class GameManager:
    def __init__(self):
        self.car = Car()
        self.plane = Plane()
        self.parking_spot = Entity(model='plane', scale=(3,1,4), color=PARKING_COLOR, position=(0,0,45))
        self.parking_box = Entity(model='cube', scale=(2.8,0.5,3.8),
                                  position=(0,0.25,45), collider='box', visible=False)
        self.obstacles = []
        self.plane_parking = Entity(model='plane', scale=(6,1,6), color=PARKING_COLOR,
                                    position=(0,0,50), collider='box', visible=False)
        self.plane_obstacles = []
        self.plane_mode = False
        self.camera_mode = 'locked'
        self.start_time = systime.time()
        self.best_time = None
        self.zoom = 0
        self.generate_obstacles()

    def generate_obstacles(self):
        # Clear old ones
        for o in self.obstacles: destroy(o)
        for o in self.plane_obstacles: destroy(o)
        self.obstacles.clear()
        self.plane_obstacles.clear()

        # Car obstacles arranged in rows forcing path
        for z in range(-40, 40, 10):
            gap_x = random.choice([-4, -2, 0, 2, 4])  # random gap
            for x in [-4, -2, 0, 2, 4]:
                if x != gap_x:
                    self.obstacles.append(Entity(model='cube', color=OBSTACLE_COLOR, scale=(1,1,1),
                                                 position=(x,0.5,z), collider='box'))

        # Plane obstacles randomized in air
        for _ in range(10):
            self.plane_obstacles.append(Entity(model='sphere', color=color.azure, scale=1,
                                               position=(random.uniform(-10,10),random.uniform(2,8),
                                                         random.uniform(-30,40)), collider='box', visible=False))

    def reset(self):
        message.text = ''
        self.start_time = systime.time()
        self.generate_obstacles()
        if self.plane_mode:
            self.plane.reset()
        else:
            self.car.reset()
            self.parking_spot.color = PARKING_COLOR

    def toggle_mode(self):
        self.plane_mode = not self.plane_mode
        if self.plane_mode:
            self.car.visible = False
            for o in self.obstacles: o.visible = False
            self.parking_spot.visible = False
            self.plane.visible = True
            self.plane_parking.visible = True
            for o in self.plane_obstacles: o.visible = True
        else:
            self.car.visible = True
            for o in self.obstacles: o.visible = True
            self.parking_spot.visible = True
            self.plane.visible = False
            self.plane_parking.visible = False
            for o in self.plane_obstacles: o.visible = False
        self.reset()

    def toggle_camera_mode(self):
        modes = ['locked','chase','cinematic']
        idx = modes.index(self.camera_mode)
        self.camera_mode = modes[(idx+1)%len(modes)]

    def is_car_parked(self):
        hit = self.car.intersects()
        if hit.hit and hit.entity == self.parking_box:
            ang = self.car.rotation_y % 360
            return abs(ang-0)<15 or abs(ang-360)<15
        return False

    def update(self):
        dt = time.dt
        elapsed = systime.time()-self.start_time
        timer_text.text = f'Time: {elapsed:.1f}'
        mode_text.text = f"Mode: {'Plane' if self.plane_mode else 'Car'} (Cam: {self.camera_mode.title()})"
        zoom_text.text = f"Zoom: {self.zoom}"

        if not self.plane_mode:
            crashed = self.car.update_move(dt, self.obstacles)
            self.car.update_camera(dt, self.camera_mode, self.zoom)
            if crashed:
                message.text = '💥 Crash!'
                invoke(self.reset, delay=2)
                return
            if self.is_car_parked():
                message.text = '✅ Perfect Parking!'
                t = systime.time()-self.start_time
                if self.best_time is None or t<self.best_time:
                    self.best_time = t
                best_time_text.text = f"Best: {self.best_time:.1f}"
                invoke(self.reset, delay=3)
        else:
            crashed = self.plane.update_move(dt, self.plane_obstacles)
            self.plane.update_camera(dt, self.camera_mode, self.zoom)
            if crashed:
                message.text = '💥 Crash!'
                invoke(self.reset, delay=2)
                return
            if self.plane.intersects(self.plane_parking).hit:
                if self.plane.velocity.length()<2 and self.plane.y<1.5:
                    message.text = '✅ Perfect Landing!'
                    t = systime.time()-self.start_time
                    if self.best_time is None or t<self.best_time:
                        self.best_time = t
                    best_time_text.text = f"Best: {self.best_time:.1f}"
                    invoke(self.reset, delay=3)
                else:
                    message.text = '⚠ Too fast!'
        speed_text.text = f'Speed: {int((self.plane.velocity if self.plane_mode else self.car.velocity).length()*10)} km/h'

manager = GameManager()

def input(key):
    if key=='r': manager.reset()
    if key=='c': manager.toggle_mode()
    if key=='v': manager.toggle_camera_mode()
    if key=='q': manager.zoom = clamp(manager.zoom-1, -3, 15)
    if key=='e': manager.zoom = clamp(manager.zoom+1, -3, 15)

def update():
    manager.update()

manager.reset()
app.run()
