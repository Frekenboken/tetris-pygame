import os
import random
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

player = None


def game_over_screen(score):
    intro_text = ["ИГРА ОКОНЧЕНА", "",
                  f"Ваш счет: {score}",
                  "Нажмите R для перезапуска",
                  "Нажмите Q для выхода"]

    # fon = pygame.transform.scale(load_image('Default.jpg'), (WIDTH, HEIGHT))
    fon = pygame.surface.Surface(WIDTH, HEIGHT)
    fon.fill(colors.BLUE)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True  # Перезапуск игры
                elif event.key == pygame.K_q:
                    terminate()  # Выход из игры
        pygame.display.flip()
        clock.tick(FPS)


def start_screen():
    intro_text = ["ЗАСТАВКА", "",
                  "Правила игры",
                  "Если в правилах несколько строк,",
                  "приходится выводить их построчно"]

    fon = pygame.transform.scale(load_image('start.png'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 50
    # for line in intro_text:
    #     string_rendered = font.render(line, 1, colors.WHITE)
    #     intro_rect = string_rendered.get_rect()
    #     text_coord += 10
    #     intro_rect.top = text_coord
    #     intro_rect.x = 10
    #     text_coord += intro_rect.height
    #     screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if pygame.rect.Rect(380, 265, 240, 70).collidepoint(event.pos):
                        return 1
                    elif pygame.rect.Rect(380, 393, 240, 70).collidepoint(event.pos):
                        return 2
        pygame.display.flip()
        clock.tick(FPS)


# Размер клетки по умолчанию
CELL_SIZE = 30


class Segment(pygame.sprite.Sprite):
    def __init__(self, sprite_group, pos_x, pos_y, color, scale=1.0):
        super().__init__(sprite_group)
        self.scale = scale
        self.image = pygame.Surface((int(28 * scale), int(28 * scale)))
        self.image.fill(color)
        self.x, self.y = pos_x, pos_y
        self.rect = self.image.get_rect().move(self.x * CELL_SIZE * scale + 1, self.y * CELL_SIZE * scale + 1)

    def move(self, x, y, cell_based=True):
        if cell_based:
            self.x += x
            self.y += y
            self.rect = self.rect.move(x * CELL_SIZE * self.scale, y * CELL_SIZE * self.scale)
        else:
            self.rect = self.rect.move(x, y)

    def set_position(self, x, y, cell_based=True):
        if cell_based:
            self.x, self.y = x, y
            self.rect = self.image.get_rect().move(x * CELL_SIZE * self.scale + 1, y * CELL_SIZE * self.scale + 1)
        else:
            self.rect.topleft = (x, y)


class Shape(pygame.sprite.Group):
    def __init__(self, shape, color, scale=1.0):
        super().__init__()
        self.shape = shape
        self.color = color
        self.scale = scale
        self.x, self.y = 0, 0

        self.make()

    def make(self):
        self.empty()
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    Segment(self, self.x + x, self.y + y, self.color, self.scale)

    def move(self, x, y, cell_based=True):
        if cell_based:
            self.x += x
            self.y += y
        for segment in self:
            segment.move(x, y, cell_based)

    def set_position(self, x, y, cell_based=True):
        if cell_based:
            self.x, self.y = x, y
        self.make()
        for segment in self:
            segment.set_position(self.x + (segment.x - self.x), self.y + (segment.y - self.y), cell_based)

    def set_scale(self, scale):
        self.scale = scale
        self.make()


class Field(Surface):
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width = width
        self.height = height
        self.board = [[0] * width for _ in range(height)]
        self.cell_size = cell_size

        self.cells = pygame.sprite.Group()
        self.next_shape = self.get_random_shape()
        self.shape: Shape | None = None
        super().__init__((width * self.cell_size, height * self.cell_size))

        self.last_fall_time = time.time()
        self.tick = 0.7
        self.score = 0
        self.run = False

    def draw(self, surface):
        self.fill(colors.BLACK)
        cell = self.cell_size
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(self, colors.GRAY, (cell * x, cell * y, cell, cell), width=1)
        self.cells.draw(self)
        self.shape.draw(self)

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

    def update(self):
        if self.run:
            if time.time() - self.last_fall_time > self.tick:
                self.shape.move(0, 1)

                if self.is_shape_collide(self.shape):
                    self.shape.move(0, -1)

                    if self.shape.y == 0:
                        self.run = False
                        return self.score

                    self.cells.add(self.shape.sprites())
                    self.new_shape()

                self.last_fall_time = time.time()

                self.score += 1

            for row in range(self.height - 1, 1, -1):
                cells = []
                for cell in self.cells:
                    if cell.y == row:
                        cells.append(cell)
                if len(cells) == self.width:
                    for cell in cells:
                        cell.kill()
                    for cell in self.cells:
                        if cell.y < row:
                            cell.move(0, 1)


        else:
            self.run = False

        return self.score

    def start(self):
        self.run = True
        self.new_shape()

    def get_random_shape(self):
        return Shape(tetris_shapes[random.choice(list(tetris_shapes.keys()))], colors.WHITE)

    def new_shape(self):
        self.shape = self.next_shape
        self.next_shape = self.get_random_shape()

    def action_left(self):
        self.shape.move(-1, 0)
        if self.is_shape_collide(self.shape):
            self.shape.move(1, 0)

    def action_right(self):
        self.shape.move(1, 0)
        if self.is_shape_collide(self.shape):
            self.shape.move(-1, 0)

    def action_rotate(self):
        x, y = self.shape.x, self.shape.y
        new_shape = Shape(rotate_matrix(self.shape.shape), colors.WHITE)
        new_shape.move(x, y)
        if self.is_shape_collide(new_shape):
            new_shape.move(1, 0)
            if self.is_shape_collide(new_shape):
                new_shape.move(-2, 0)
            if self.is_shape_collide(new_shape):
                return
        self.shape = new_shape

    def is_shape_collide(self, shape):
        other_cells = self.cells.copy()
        for cell in shape:
            other_cells.remove(cell)
        if pygame.sprite.groupcollide(shape, other_cells, False, False):
            return True
        for cell in shape:
            if not (0 <= cell.x < self.width) or not (0 <= cell.y < self.height):
                return True

    def set_tick(self, tick):
        self.tick = tick


clock = pygame.time.Clock()

f1 = pygame.font.Font(None, 80)

while True:
    mode = start_screen()

    game_running = True

    field = Field(WIDTH // 2 - (field_width // 2 * cell_size), - 2 * cell_size, field_width, field_height + 2)

    field.start()

    while game_running:
        screen.fill(colors.BLACK)

        score = field.update()
        field.draw(screen)
        text1 = f1.render(str(score), True, colors.WHITE)
        screen.blit(text1, (20, 15))

        pygame.draw.rect(screen, colors.WHITE, (WIDTH / 3 * 2 + (WIDTH / 3 - 150) / 2, HEIGHT / 2 - 150 / 2, 150, 150),
                         width=1)
        shape_preview = Shape(field.next_shape.shape, field.next_shape.color)
        shape_preview.move(WIDTH / 3 * 2 + (WIDTH / 3 - 150) / 2 + 30, HEIGHT / 2 - 150 / 2 + 30, cell_based=False)
        shape_preview.draw(screen)

        menu_button = pygame.draw.rect(screen, colors.WHITE, (WIDTH / 3 / 4, HEIGHT * 0.85, WIDTH / 3 / 2, 50))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                field.action_left()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                field.action_right()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                field.action_rotate()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                field.set_tick(0.05)
            if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
                field.set_tick(0.7)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    print(pygame.rect.Rect(380, 265, 240, 70).collidepoint(event.pos))
                    if menu_button.collidepoint(event.pos):
                        game_running = False

        if not field.run:
            if game_over_screen(score):
                field = Field(WIDTH // 2 - (field_width // 2 * cell_size), - 2 * cell_size, field_width,
                              field_height + 2)
                field.start()
            else:
                terminate()

        pygame.display.flip()
        clock.tick(FPS)
