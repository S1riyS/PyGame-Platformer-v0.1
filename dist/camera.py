import pygame
vec = pygame.math.Vector2
from abc import ABC, abstractmethod
from data import *

class Camera:
    def __init__(self, player, width, height):
        self.player = player
        self.WIDTH, self.HEIGHT = width, height

        self.offset = vec(0, 0)
        self.offset_float = vec(0, 0)
        self.CONST = vec(-(self.WIDTH / 3), -(self.HEIGHT - self.player.rect.height) / 2)

    def setmethod(self, method):
        self.method = method

    def scroll(self):
        self.method.scroll()

class CamScroll(ABC):
    def __init__(self, camera, player):
        self.camera = camera
        self.player = player

    @abstractmethod
    def scroll(self):
        pass

class Follow(CamScroll):
    def __init__(self, camera, player, smooth):
        CamScroll.__init__(self, camera, player)
        self.smooth = smooth


    def scroll(self):
        self.camera.offset_float.x += (self.player.rect.x - self.camera.offset_float.x + self.camera.CONST.x) // self.smooth
        self.camera.offset_float.y += (self.player.rect.y - self.camera.offset_float.y + self.camera.CONST.y) // self.smooth
        self.camera.offset.x, self.camera.offset.y = int(self.camera.offset_float.x), int(self.camera.offset_float.y)

class Border(CamScroll):
    def __init__(self, camera, player):
        CamScroll.__init__(self, camera, player)

    def scroll(self):
        self.camera.offset_float.x += (self.player.rect.x - self.camera.offset_float.x + self.camera.CONST.x)
        self.camera.offset_float.y += (self.player.rect.y - self.camera.offset_float.y + self.camera.CONST.y)
        self.camera.offset.x, self.camera.offset.y = int(self.camera.offset_float.x), int(self.camera.offset_float.y)
        self.camera.offset.x = max(self.player.left_border, self.camera.offset.x)
        self.camera.offset.x = min(self.camera.offset.x, self.player.right_border - self.camera.WIDTH)

class Auto(CamScroll):
    def __init__(self,camera, player, speed):
        CamScroll.__init__(self,camera, player)
        self.speed = speed

    def scroll(self):
        self.camera.offset.x += self.speed
