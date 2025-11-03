# ==========================
# ADVANCED 3D PARKING GAME IN PYTHON
# by ChatGPT (GPT-5) 😎
# ==========================

from ursina import *
import math
import random

app = Ursina()

window.title = "3D Parking Game"
window.borderless = False
window.exit_button.visible = False
window.fullscreen = False
window.fps_counter.enabled = True

# Global variables
player = None
sun = None
ambient = None
park_zone = None
walls = []
trees = []
ai_cars = []
info_text = None


# ===========================================================
# MAIN MENU
# ===========================================================
def start_game():
    destroy(menu)
    create_game_scene()

def open_settings():
    destroy(menu)
    show_settings_menu()

def choose_level():
    print("Level system coming soon...")

def quit_game():
    application.quit()


def create_main_menu():
    global menu
    menu = Entity()

    # Title Text
    Text("🚗 3D Parking Game 🚗", parent=menu, y=0.35, scale=2, color=color.orange)
    Text("By ChatGPT (GPT-5)", parent=menu, y=0.25, scale=1, color=color.white)

    # Buttons
    Button("Start Game", parent=menu, y=0.1, color=color.azure, scale=(0.3, 0.1), on_click=start_game)
    Button("Settings", parent=menu, y=-0.1, color=color.green, scale=(0.3, 0.1), on_click=open_settings)
    Button("Levels", parent=menu, y=-0.3, color=color.yellow, scale=(0.3, 0.1), on_click=choose_level)
    Button("Quit", parent=menu, y=-0.5, color=color.red, scale=(0.3, 0.1), on_click=quit_game)

create_main_menu()


# ===========================================================
# SETTINGS WINDOW
# ===========================================================
def show_settings_menu():
    settings = Entity()

    Text("⚙️ Settings ⚙️", parent=settings, y=0.35, scale=2, color=color.azure)
    Text("W/A/S/D to Move", parent=settings, y=0.15, scale=1.2)
    Text("Park inside the green zone", parent=settings, y=-0.05, scale=1.2)
    Text("Avoid AI cars and trees!", parent=settings, y=-0.2, scale=1.2, color=color.orange)

    Button("Back", parent=settings, y=-0.4, color=color.red, scale=(0.3, 0.1),
           on_click=lambda: [destroy(settings), create_main_menu()])


# ===========================================================
# GAME ENVIRONMENT
# ===========================================================
def create_game_scene():
    global player, sun, ambient, park_zone, walls, ai_cars, trees, info_text

    # Ground
    ground = Entity(model='plane', scale=60, color=color.gray, collider='box')

    # Parking zone
    park_zone = Entity(model='cube', color=color.lime, scale=(3, 0.05, 6), position=(10, 0, 0))

    # Walls / Boundaries
    walls.clear()
    for pos in [(-25, 1, 0), (25, 1, 0), (0, 1, -25), (0, 1, 25)]:
        wall = Entity(model='cube', color=color.dark_gray,
                      scale=(1, 2, 50) if abs(pos[0]) > 0 else (50, 2, 1),
                      position=pos, collider='box')
        walls.append(wall)

    # Trees (decorations)
    trees.clear()
    for i in range(15):
        x = random.randint(-20, 20)
        z = random.randint(-20, 20)
        trunk = Entity(model='cube', color=color.brown, scale=(0.3, 2, 0.3), position=(x, 1, z))
        leaves = Entity(model='sphere', color=color.green, scale=1.8, position=(x, 2.5, z))
        trees.extend([trunk, leaves])

    # AI Cars
    ai_cars.clear()
    for i in range(3):
        pos = (random.randint(-10, 10), 0.25, random.randint(-10, 10))
        car = Entity(model='cube', color=color.azure, scale=(1, 0.5, 2), position=pos, collider='box')
        ai_cars.append(car)

    # Player Car
    player = Entity(model='cube', color=color.red, scale=(1, 0.5, 2), position=(0, 0.25, -10), collider='box')
    # Wheels
    for wx, wz in [(-0.4, 0.9), (0.4, 0.9), (-0.4, -0.9), (0.4, -0.9)]:
        Entity(model='cylinder', color=color.black, scale=(0.3, 0.3, 0.3),
               position=(player.x + wx, 0.15, player.z + wz), rotation_x=90, parent=player)

    # Camera setup
    camera.parent = player
    camera.position = (0, 3, -8)
    camera.rotation_x = 15

    # Lights (sun & ambient)
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -1, -1))
    ambient = AmbientLight(color=color.rgb(150, 150, 150))

    # Info text
    info_text = Text("Use W, A, S, D | Park in the green zone | Avoid AI Cars", y=0.45, scale=1.2, color=color.white)

    # Cinematic start
    cinematic_intro()

    # Start AI movement
    invoke(move_ai_cars, delay=1)

    # Run update loop
    def update():
        handle_player_movement()
        handle_collisions()
        update_day_night()
        move_ai_cars()
        check_parking()

    app.run()


# ===========================================================
# PLAYER MOVEMENT
# ===========================================================
def handle_player_movement():
    speed = 5 * time.dt
    rotation_speed = 60 * time.dt

    if held_keys['w']:
        player.position += player.forward * speed
    if held_keys['s']:
        player.position -= player.forward * speed
    if held_keys['a']:
        player.rotation_y += rotation_speed * 30
    if held_keys['d']:
        player.rotation_y -= rotation_speed * 30


# ===========================================================
# COLLISIONS
# ===========================================================
def handle_collisions():
    for obj in walls + ai_cars + trees:
        if hasattr(obj, 'collider') and player.intersects(obj).hit:
            player.position -= player.forward * 0.2  # bounce back
            Audio('assets/hit.wav', autoplay=True) if hasattr(Audio, '__call__') else None


# ===========================================================
# AI CARS MOVEMENT
# ===========================================================
def move_ai_cars():
    for car in ai_cars:
        car.x += math.sin(time.time() + id(car)) * 0.02  # small left-right movement
        car.z += math.cos(time.time() + id(car)) * 0.02  # small front-back movement


# ===========================================================
# PARKING SUCCESS
# ===========================================================
def check_parking():
    if distance(player.position, park_zone.position) < 1.5:
        Text("✅ YOU PARKED SUCCESSFULLY!", origin=(0, 0), y=0.3, scale=2, color=color.lime, duration=3)
        invoke(return_to_menu, delay=4)


def return_to_menu():
    destroy(player)
    destroy(sun)
    destroy(ambient)
    for o in walls + trees + ai_cars:
        destroy(o)
    create_main_menu()


# ===========================================================
# DAY / NIGHT CYCLE
# ===========================================================
t = 0
def update_day_night():
    global t, sun, ambient
    t += time.dt * 0.1
    brightness = (math.sin(t) + 1) / 2  # 0 to 1
    sun.color = color.rgb(255 * brightness, 255 * brightness, 200)
    sun.look_at(Vec3(math.sin(t) * 5, -1, math.cos(t) * 5))  # move sun in arc
    ambient.color = color.rgb(60 + 150 * brightness, 60 + 150 * brightness, 100 + 80 * brightness)


# ===========================================================
# CINEMATIC INTRO
# ===========================================================
def cinematic_intro():
    camera.position = (0, 20, -30)
    camera.look_at((0, 0, 0))
    invoke(lambda: camera.animate_position((0, 3, -8), duration=3, curve=curve.in_out_sine), delay=1)


app.run()
