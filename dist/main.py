################ ИМПОРТ МОДУЛЕЙ ################
import pygame
from pygame.locals import *
from pygame.math import Vector2
from math import sqrt, atan2, cos, sin

from data import *
from camera import *

################ НАСТРОЙКИ ОКНА ################
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(CAPTION)
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)

display = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
display.fill((22, 22, 22))

tile_rects = []

scope = pygame.image.load('Assets/scope.png')
scope_rect = scope.get_rect()

################ ГРУППЫ СПРАЙТОВ ################
all_sprites = pygame.sprite.Group()
map_sprites = pygame.sprite.Group()
player_sprite = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()


def collision_test(rect, tiles_list):
    hit_list = []
    for tile in tiles_list:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list

################ КАРТА УРОВНЯ ################
class Map(pygame.sprite.Sprite):
    def __init__(self, map_folder_name):
        super().__init__(map_sprites)

        self.background_image = pygame.image.load(f'{map_folder_name}/background2.jpg').convert()
        self.background_image = pygame.transform.scale(self.background_image, (SURFACE_WIDTH, SURFACE_HEIGHT))

        self.grass_img = pygame.image.load(f'{map_folder_name}/Tiles/grass.png').convert()
        self.earth_img = pygame.image.load(f'{map_folder_name}/Tiles/earth.png').convert()

        with open(f'{map_folder_name}/map.txt') as file:
            self.map_data = [[int(i) for i in row] for row in file.read().split('\n')]

    def update(self):
        display.blit(self.background_image, (0, 0))

        # xOffset, yOffset = camera.camera_move()
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile:
                    self.tile_x = x * TILE_SIDE
                    self.tile_y = y * TILE_SIDE
                    if tile == 1:
                        self.tile_image = self.earth_img
                    elif tile == 2:
                        self.tile_image = self.grass_img

                    display.blit(self.tile_image, (self.tile_x - camera.offset.x, self.tile_y - camera.offset.y))
                    tile_rects.append(pygame.Rect(self.tile_x, self.tile_y, TILE_SIDE, TILE_SIDE))

################ ПЕРСОНАЖ ################
class Player(pygame.sprite.Sprite):
    def __init__(self, player_image_name):
        super().__init__(player_sprite)

        self.image = pygame.image.load(player_image_name) # Спрайт
        self.rect = self.image.get_rect() # Rect персонажа
        # Начальные координаты
        self.rect.y = 3 * (SURFACE_HEIGHT / HEIGHT) * TILE_SIDE
        self.rect.x = 5 * (SURFACE_HEIGHT / HEIGHT) * TILE_SIDE

        # Размер персонажа
        self.width, self.height = self.rect.size
        self.orientation = 'right'

        # Параметры движения по оси Ox
        self.moving_right, self.moving_left = False, False
        self.speed = 2
        self.acceleration = 0.1

        # Параметры прыжка (различные коэффициенты для более гибкой настройки высоты прыжка и тп)
        self.is_jump = False
        self.jump_force = 40
        self.jump_count = 0
        self.jump_coef = 0.2
        self.gravity = 1

    # Перемещение перосонажа по обоим осям + коллизия с картой
    def player_move(self, tiles):
        self.rect.x += self.movement[0]
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if self.movement[0] > 0:
                self.rect.right = tile.left
                self.collisions_types['right'] = True

            elif self.movement[0] < 0:
                self.rect.left = tile.right
                self.collisions_types['left'] = True

        self.rect.y += self.movement[1]
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if self.movement[1] > 0:
                self.rect.bottom = tile.top
                self.is_jump = False
                self.collisions_types['bottom'] = True

            elif self.movement[1] < 0:
                self.rect.top = tile.bottom
                self.is_jump = False
                self.collisions_types['top'] = True

    # Прыдок
    def jump(self):
        if self.is_jump:
            if self.jump_count >= 0:
                self.movement[1] -= self.jump_count * self.jump_coef
                self.jump_count -= 1
            else:
                self.is_jump = False

    # Отрисовываем персонажа
    def blit_player(self):
        # xOffset, yOffset = camera.camera_move(is_offset_int=True)
        # print(xOffset, yOffset)

        x, y = self.rect.x - camera.offset.x, self.rect.y - camera.offset.y
        if self.orientation == 'right':
            display.blit(self.image, (x, y))
        elif self.orientation == 'left':
            display.blit(pygame.transform.flip(self.image, True, False), (x, y))

    # Цикл персонажа
    # Цикл персонажа
    def update(self):
        self.movement = [0, 0] # Скорость перемещения перосонажа по обоим осям
        self.collisions_types = {'top': False, 'bottom': False, 'left': False, 'right': False}

        # Перемещение влево/право
        if self.moving_right:
            self.movement[0] += self.speed
        if self.moving_left:
            self.movement[0] -= self.speed

        # Гравитация
        self.movement[1] += self.gravity
        self.gravity += self.acceleration
        # Устанавливаем максимальное значение гравитации
        if self.movement[1] > 3:
            self.movement[1] = 3

        self.jump()
        self.player_move(tile_rects)

        self.blit_player()

################ ПРИЦЕЛ ################
class Scope(pygame.sprite.Sprite):
    def __init__(self, scope_image_name):
        super().__init__(player_sprite)
        self.image = pygame.image.load(scope_image_name)
        self.rect = self.image.get_rect()

    def update(self):
        mouse_position = pygame.mouse.get_pos()
        self.rect.centerx = mouse_position[0] * (SURFACE_WIDTH / WIDTH)
        self.rect.centery = mouse_position[1] * (SURFACE_HEIGHT / HEIGHT)
        display.blit(self.image, self.rect)


################ ПУЛЯ ################
class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet_image_name, start_position, finish_position, speed):
        super().__init__(bullet_group)
        self.image = pygame.image.load(bullet_image_name)
        self.rect = self.image.get_rect()

        self.x, self.y = start_position
        self.start_position = (start_position[0] - camera.offset.x, start_position[1] - camera.offset.y)
        self.finish_position = finish_position
        self.speed = speed

        self.dx = self.finish_position[0] - self.start_position[0]
        self.dy = self.finish_position[1] - self.start_position[1]
        self.angle = atan2(self.dy, self.dx)

    def destroy(self):
        # if (self.x < 0 - camera.offset.x or self.x - camera.offset.x > SURFACE_WIDTH) or \
        #         (self.y - camera.offset.x < 0 or self.y - camera.offset.x > SURFACE_HEIGHT):
        #     self.kill()
        pass

    def update(self):
        self.x += self.speed * cos(self.angle)
        self.y += self.speed * sin(self.angle)

        display.blit(self.image, (self.x - camera.offset.x, self.y - camera.offset.y))

        self.destroy()

################ КАРТА ########ы########
Map(map_folder_name='Assets/Maps/Map1')

################ ПЕРСОНАЖ ################
player = Player(player_image_name='Assets/player.png') # Персонаж
scope = Scope(scope_image_name='Assets/scope.png')

################ КАМЕРА ################
camera = Camera(player=player, width=SURFACE_WIDTH, height=SURFACE_HEIGHT)
follow = Follow(camera, player, smooth=25)
border = Border(camera, player)
auto = Auto(camera, player, speed=1)
camera.setmethod(follow)


################ ИГРОВОЙ ЦИКЛ ################
run = True
while run:
    tile_rects = []
    map_sprites.update()

    for event in pygame.event.get():
        if event.type == QUIT:
            run = False

        ################ СОБЫТИЯ КЛАВИАТУРЫ ################
        if event.type == pygame.KEYDOWN:
            if  event.key == K_d:
                player.moving_right = True
                player.orientation = 'right'
            if  event.key == K_a:
                player.moving_left = True
                player.orientation = 'left'
            if event.key == K_SPACE:
                if player.collisions_types['bottom']:
                    player.is_jump = True
                    player.jump_count = player.jump_force

        if event.type == pygame.KEYUP:
            if event.key == K_d:
                player.moving_right = False
            if event.key == K_a:
                player.moving_left = False

        ################ СОБЫТИЯ МЫШИ ################
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                Bullet(bullet_image_name='Assets/bullet.png', start_position=player.rect.center, finish_position=scope.rect.center, speed=3)

    ################ ОБНОВЛЕНИЕ/АНИМАЦИЯ СПРАЙТОВ ################
    all_sprites.update()
    player_sprite.update()
    bullet_group.update()
    camera.scroll()

    # Растягиваем display на весь screen
    surface = pygame.transform.scale(display, WINDOW_SIZE)#WINDOW_SIZE
    screen.blit(surface, (0, 0))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()