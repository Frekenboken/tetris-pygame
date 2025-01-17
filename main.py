import os
import sys
import time

import numpy as np
import pygame
from pygame import Surface

from pygame_utils import terminate, load_level, load_image
from utils import rotate_matrix
from figures import tetris_shapes
import colors

field_size = field_width, field_height = (10, 20)
cell_size = 30
SIZE = WIDTH, HEIGHT = (1000, 600)
FPS = 50
pygame.init()
pygame.display.set_caption("Перемещение героя")
screen = pygame.display.set_mode(SIZE)

all_sprites = pygame.sprite.Group()
box_group = pygame.sprite.Group()

tile_width = tile_height = 50

player = None


def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]

    fon = pygame.transform.scale(load_image('fon.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(FPS)


def generate_level(level):
    new_player, x, y = None, None, None
    player_x, player_y = None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Box('wall', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                player_x, player_y = x, y
    new_player = Player(player_x, player_y)
    return new_player, x, y


class Shape(pygame.sprite.Sprite):
    def __init__(self, block_size, shape, color):
        super().__init__()
        self.block_size = block_size
        self.shape = shape
        self.color = color
        self.image = self.create_image()
        self.rect = self.image.get_rect()

        self.size = (self.rect.width // self.block_size, self.rect.height // self.block_size)
        self.width = self.size[0]
        self.height = self.size[1]

    def create_image(self):
        width = len(self.shape[0]) * self.block_size
        height = len(self.shape) * self.block_size
        image = pygame.Surface((width, height), pygame.SRCALPHA)
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(image, self.color,
                                     pygame.Rect(x * self.block_size + 1 , y * self.block_size + 1, self.block_size - 2,
                                                 self.block_size - 2))
        return image

    def rotate(self):
        self.shape = rotate_matrix(self.shape)
        self.image = self.create_image()

    def fall(self):
        self.rect = self.rect.move(0, self.block_size)

    def move_right(self):
        self.rect = self.rect.move(self.block_size, 0)

    def move_left(self):
        self.rect = self.rect.move(-self.block_size, 0)

    def move(self, cell_x, cell_y):
        self.rect = self.rect.move(cell_x * self.block_size, cell_y * self.block_size)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)


class Field(Surface):
    # создание поля
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width = width
        self.height = height
        self.board = [[0] * width for _ in range(height)]
        self.cell_size = cell_size

        self.shapes = []
        self.active_shape: Shape | None = None
        super().__init__((width * self.cell_size, height * self.cell_size))

        self.last_fall_time = time.time()

    def draw(self, surface):
        self.fill(colors.BLACK)
        cell = self.cell_size
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(self, colors.GRAY, (cell * x, cell * y, cell, cell), width=1)
        for shape in self.shapes:
            shape.draw(self)

        surface.blit(self, (self.x, self.y))

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        if cell:
            self.on_click(cell)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos[0], mouse_pos[1]
        x, y = x // self.cell_size, y // self.cell_size

        if not (0 <= x < self.width and 0 <= y < self.height):
            return None
        return x, y

    def on_click(self, cell):
        print(cell)

    def new_shape(self, shape, color):
        new_shape = Shape(self.cell_size, shape, color)
        new_shape.move(self.width // 2 - new_shape.width // 2, 0)
        self.shapes.append(new_shape)
        self.active_shape = new_shape

        new_shape = Shape(self.cell_size, shape, color)
        new_shape.move(self.width // 2 - new_shape.width // 2, 10)
        self.shapes.append(new_shape)

    def update(self):
        if self.active_shape.rect.collidelistall(self.shapes):

            self.shapes.append(self.active_shape)
            self.new_shape(tetris_shapes["L"], colors.BLUE)
        if time.time() - self.last_fall_time > 0.7:
            self.active_shape.fall()
            self.last_fall_time = time.time()

    def start(self):
        self.new_shape(tetris_shapes["L"], colors.BLUE)

field = Field(WIDTH // 2 - (field_width // 2 * cell_size), - 2 * cell_size, field_width, field_height + 2)

field.start()

clock = pygame.time.Clock()

# start_screen()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            field.active_shape.move_left()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            field.active_shape.move_right()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                # all_sprites.update(event.pos)
                field.get_click(event.pos)
        if event.type == pygame.MOUSEWHEEL:
            pass

    screen.fill(colors.BLACK)

    field.update()
    field.draw(screen)

    # all_sprites.draw(screen)
    # all_sprites.update()
    # box_group.draw(screen)
    # box_group.update()
    # player_group.draw(screen)
    # player_group.update()
    pygame.display.flip()
    clock.tick(FPS)
