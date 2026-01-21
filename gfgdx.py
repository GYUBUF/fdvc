from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

# Настройки окна
window.title = '3D Шутер'
window.fullscreen = False
window.exit_button.visible = False

# Переменные игры
player_health = 100
score = 0
enemies = []
bullets = []
game_over = False

# Текстуры и цвета
Sky(color=color.rgb(135, 206, 235))

# Создаём землю
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    color=color.rgb(34, 139, 34),
    texture='white_cube',
    texture_scale=(50, 50),
    collider='box'
)

# Стены арены
walls = []
wall_positions = [
    (0, 2.5, 50, 100, 5, 1),
    (0, 2.5, -50, 100, 5, 1),
    (50, 2.5, 0, 1, 5, 100),
    (-50, 2.5, 0, 1, 5, 100)
]

for pos in wall_positions:
    wall = Entity(
        model='cube',
        position=(pos[0], pos[1], pos[2]),
        scale=(pos[3], pos[4], pos[5]),
        color=color.rgb(139, 69, 19),
        texture='brick',
        collider='box'
    )
    walls.append(wall)

# Создаём укрытия
for i in range(15):
    box = Entity(
        model='cube',
        position=(random.uniform(-40, 40), 1.5, random.uniform(-40, 40)),
        scale=(random.uniform(2, 5), 3, random.uniform(2, 5)),
        color=color.rgb(100, 100, 100),
        texture='white_cube',
        collider='box'
    )

# Игрок
player = FirstPersonController(
    position=(0, 2, 0),
    speed=8,
    jump_height=2,
    mouse_sensitivity=Vec2(100, 100)
)
player.cursor.color = color.red
player.cursor.scale = 0.01

# Оружие (визуальное)
gun = Entity(
    parent=camera,
    model='cube',
    scale=(0.15, 0.15, 0.6),
    position=(0.4, -0.3, 0.5),
    color=color.dark_gray,
    rotation=(0, 0, 0)
)

gun_barrel = Entity(
    parent=gun,
    model='cube',
    scale=(0.3, 0.3, 0.5),
    position=(0, 0, 0.7),
    color=color.gray
)

# UI элементы
health_bar_bg = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.4, 0.03),
    position=(-0.55, 0.45),
    color=color.dark_gray
)

health_bar = Entity(
    parent=camera.ui,
    model='quad',
    scale=(0.4, 0.03),
    position=(-0.55, 0.45),
    color=color.red,
    origin=(-0.5, 0)
)

health_text = Text(
    text=f'HP: {player_health}',
    position=(-0.75, 0.47),
    scale=1.5,
    color=color.white
)

score_text = Text(
    text=f'Счёт: {score}',
    position=(-0.75, 0.40),
    scale=1.5,
    color=color.yellow
)

ammo_text = Text(
    text='ЛКМ - Стрелять | WASD - Движение | SPACE - Прыжок',
    position=(0, -0.45),
    origin=(0, 0),
    scale=1,
    color=color.white
)

crosshair = Text(
    text='+',
    position=(0, 0),
    origin=(0, 0),
    scale=2,
    color=color.red
)

game_over_text = Text(
    text='',
    position=(0, 0),
    origin=(0, 0),
    scale=3,
    color=color.red,
    enabled=False
)


# Класс врага
class Enemy(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1, 2, 1),
            position=position,
            collider='box'
        )
        self.health = 30
        self.speed = random.uniform(2, 4)
        self.damage = 10
        self.attack_cooldown = 0
        
        # Глаза врага
        self.eye1 = Entity(
            parent=self,
            model='cube',
            color=color.yellow,
            scale=(0.2, 0.2, 0.1),
            position=(-0.25, 0.3, 0.5)
        )
        self.eye2 = Entity(
            parent=self,
            model='cube',
            color=color.yellow,
            scale=(0.2, 0.2, 0.1),
            position=(0.25, 0.3, 0.5)
        )
    
    def update(self):
        if not game_over and player.enabled:
            # Движение к игроку
            direction = (player.position - self.position).normalized()
            direction.y = 0
            
            self.position += direction * self.speed * time.dt
            self.look_at_2d(player.position, 'y')
            
            # Атака игрока при близком расстоянии
            dist = distance(self, player)
            if dist < 2:
                self.attack_cooldown -= time.dt
                if self.attack_cooldown <= 0:
                    self.attack()
                    self.attack_cooldown = 1
    
    def attack(self):
        global player_health
        player_health -= self.damage
        update_health_ui()
        
        # Эффект урона
        camera.shake(duration=0.2, magnitude=0.5)
    
    def take_damage(self, damage):
        global score
        self.health -= damage
        
        # Мигание при получении урона
        self.color = color.white
        invoke(setattr, self, 'color', color.red, delay=0.1)
        
        if self.health <= 0:
            self.die()
    
    def die(self):
        global score
        score += 100
        score_text.text = f'Счёт: {score}'
        
        # Эффект смерти
        for _ in range(5):
            particle = Entity(
                model='cube',
                color=color.red,
                scale=0.2,
                position=self.position,
                velocity=Vec3(
                    random.uniform(-2, 2),
                    random.uniform(1, 3),
                    random.uniform(-2, 2)
                )
            )
            destroy(particle, delay=1)
        
        if self in enemies:
            enemies.remove(self)
        destroy(self)


# Класс пули
class Bullet(Entity):
    def __init__(self, position, direction):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.15,
            position=position,
            collider='sphere'
        )
        self.direction = direction
        self.speed = 80
        self.lifetime = 2
        self.damage = 15
    
    def update(self):
        self.position += self.direction * self.speed * time.dt
        self.lifetime -= time.dt
        
        if self.lifetime <= 0:
            self.remove()
            return
        
        # Проверка попадания во врагов
        for enemy in enemies[:]:
            if self.intersects(enemy).hit:
                enemy.take_damage(self.damage)
                self.remove()
                return
        
        # Проверка столкновения со стенами/объектами
        hit_info = raycast(
            self.position,
            self.direction,
            distance=0.5,
            ignore=[self, player]
        )
        if hit_info.hit and hit_info.entity not in enemies:
            self.remove()
    
    def remove(self):
        if self in bullets:
            bullets.remove(self)
        destroy(self)


def update_health_ui():
    global player_health, game_over
    
    player_health = max(0, player_health)
    health_bar.scale_x = 0.4 * (player_health / 100)
    health_text.text = f'HP: {player_health}'
    
    if player_health <= 0:
        end_game()


def end_game():
    global game_over
    game_over = True
    player.enabled = False
    mouse.locked = False
    
    game_over_text.text = f'ИГРА ОКОНЧЕНА!\nСчёт: {score}\n\nR - Рестарт'
    game_over_text.enabled = True


def restart_game():
    global player_health, score, game_over, enemies, bullets
    
    # Удаляем всех врагов
    for enemy in enemies[:]:
        destroy(enemy)
    enemies.clear()
    
    # Удаляем все пули
    for bullet in bullets[:]:
        destroy(bullet)
    bullets.clear()
    
    # Сброс переменных
    player_health = 100
    score = 0
    game_over = False
    
    # Сброс игрока
    player.position = (0, 2, 0)
    player.enabled = True
    mouse.locked = True
    
    # Обновление UI
    update_health_ui()
    score_text.text = f'Счёт: {score}'
    game_over_text.enabled = False


def spawn_enemy():
    if not game_over and len(enemies) < 10:
        # Спавн в случайной позиции
        spawn_pos = Vec3(
            random.uniform(-40, 40),
            1,
            random.uniform(-40, 40)
        )
        
        # Не спавнить слишком близко к игроку
        while distance(spawn_pos, player.position) < 15:
            spawn_pos = Vec3(
                random.uniform(-40, 40),
                1,
                random.uniform(-40, 40)
            )
        
        enemy = Enemy(spawn_pos)
        enemies.append(enemy)


def shoot():
    global gun
    
    if game_over:
        return
    
    # Анимация отдачи
    gun.animate('position', gun.position + Vec3(0, 0, -0.1), duration=0.05)
    gun.animate('position', Vec3(0.4, -0.3, 0.5), duration=0.1, delay=0.05)
    
    # Создаём пулю
    bullet_start = camera.world_position + camera.forward * 1.5
    bullet_direction = camera.forward
    
    bullet = Bullet(bullet_start, bullet_direction)
    bullets.append(bullet)
    
    # Эффект вспышки
    muzzle_flash = Entity(
        model='sphere',
        color=color.orange,
        scale=0.3,
        position=camera.world_position + camera.forward * 2
    )
    destroy(muzzle_flash, delay=0.05)


# Спавн врагов каждые 3 секунды
def enemy_spawner():
    spawn_enemy()
    if not game_over:
        invoke(enemy_spawner, delay=3)

# Начальные враги
for _ in range(5):
    spawn_enemy()

# Запуск спавнера
invoke(enemy_spawner, delay=3)


def input(key):
    if key == 'left mouse down':
        shoot()
    
    if key == 'r':
        restart_game()
    
    if key == 'escape':
        if mouse.locked:
            mouse.locked = False
        else:
            application.quit()


def update():
    global player_health
    
    if game_over:
        return
    
    # Проверка падения
    if player.y < -10:
        player_health = 0
        update_health_ui()
    
    # Регенерация здоровья (медленная)
    if player_health < 100 and player_health > 0:
        player_health = min(100, player_health + 0.5 * time.dt)
        update_health_ui()


# Инструкция при старте
info_text = Text(
    text='3D ШУТЕР\n\nУправление:\nWASD - Движение\nПРОБЕЛ - Прыжок\nЛКМ - Стрельба\nESC - Выход\n\nКликните чтобы начать',
    position=(0, 0),
    origin=(0, 0),
    scale=1.5,
    color=color.white,
    background=True
)

def start_game():
    info_text.enabled = False
    mouse.locked = True

info_text.on_click = start_game

app.run()