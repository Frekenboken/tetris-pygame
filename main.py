import random
import time
import csv

import pygame
from pygame import Surface

from pygame_utils import terminate, load_image
from utils import rotate_matrix
from shapes import tetris_shapes
import colors

field_size = field_width, field_height = (10, 20)
CELL_SIZE = 30
SIZE = WIDTH, HEIGHT = (1000, 600)
FPS = 50

RECORDS_PATH = 'data/high_scores.csv'
PIXEL_FONT_PATH = 'data/Jersey10-Regular.ttf'
START_IMG_PATH = 'start.png'
ANIMATION_PATH = 'anim.png'

pygame.init()
pygame.display.set_caption("TETRIS")
screen = pygame.display.set_mode(SIZE)

# Звуковые эффекты
game_over_sound = pygame.mixer.Sound('data/game_over.wav')

player = None
animation_sprites = pygame.sprite.Group()


def records_add(new_record):
    with open(RECORDS_PATH, mode='r', newline='') as file:
        reader = csv.reader(file)
        records = [int(row[0]) for row in reader]

    if len(records) < 3 or new_record > min(records):
        records.append(new_record)
        records = sorted(records, reverse=True)[:3]
        with open(RECORDS_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows([[record] for record in records])


def records_read():
    try:
        with open(RECORDS_PATH, mode='r', newline='') as file:
            reader = csv.reader(file)
            records = [int(row[0]) for row in reader]
        return sorted(records, reverse=True)[:3]
    except FileNotFoundError:
        return []


def game_over_screen(score):
    game_over_sound.play()
    fon = pygame.surface.Surface((WIDTH, HEIGHT))
    fon.fill(colors.BLACK)
    screen.blit(fon, (0, 0))

    font = pygame.font.Font(PIXEL_FONT_PATH, 60)
    font_mini = pygame.font.Font(PIXEL_FONT_PATH, 30)

    score_string = font.render("Your score: " + str(score), 1, colors.WHITE)
    screen.blit(score_string, (WIDTH / 2 - score_string.get_width() / 2,
                               HEIGHT / 2 - score_string.get_height() / 2))
    timer = time.time()
    while True:
        if time.time() - timer > 2.4:

            press_string = font_mini.render("Press any button", 1, colors.WHITE)
            screen.blit(press_string,
                        (WIDTH / 2 - press_string.get_width() / 2,
                         HEIGHT / 2 - press_string.get_height() / 2 + 70))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN:
                    return True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    return True
        else:
            pygame.event.get()
        pygame.display.flip()
        clock.tick(FPS)


def start_screen():
    fon = pygame.transform.scale(load_image(START_IMG_PATH), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    animation_surface = pygame.Surface((60, 420))

    competitive_mode_button = pygame.rect.Rect(332, 113, 267, 158)
    free_mode_button = pygame.rect.Rect(334, 382, 158, 104)

    text_coord = 220
    records_font_size = 80

    for record in records_read():
        records_font = pygame.font.Font(PIXEL_FONT_PATH, records_font_size)
        string_rendered = records_font.render(str(record), 1, colors.WHITE)
        intro_rect = string_rendered.get_rect()
        intro_rect.top = text_coord
        intro_rect.x = 713 + 76 - intro_rect.width / 2
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
        records_font_size -= 10

    last_animation_time = time.time()
    while True:
        if time.time() - last_animation_time > 0.5:
            animation_surface.fill(colors.BLACK)
            animation_sprites.update()
            screen.blit(animation_surface, (194, 90))
            animation_sprites.draw(screen)
            last_animation_time = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if competitive_mode_button.collidepoint(event.pos):
                        return 1
                    elif free_mode_button.collidepoint(event.pos):
                        return 2

        pygame.display.flip()
        clock.tick(FPS)


class AnimatedSprite(pygame.sprite.Sprite):

    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(animation_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]


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

    def __init__(self, shape, color, scale=1):
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
        self.cell_size = CELL_SIZE

        self.cells = pygame.sprite.Group()
        self.next_shape = self.get_random_shape()
        self.next_shape.move(3, 0)
        self.shape: Shape | None = None
        super().__init__((width * self.cell_size, height * self.cell_size))

        self.last_fall_time = time.time()
        self.tick = 0.7
        self.score = 0
        self.timer = time.time()
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

    def start(self):
        self.run = True
        self.new_shape()

    def get_random_shape(self):
        shape = Shape(tetris_shapes[random.choice(list(tetris_shapes.keys()))], colors.WHITE)
        return shape

    def new_shape(self):
        self.shape = self.next_shape
        self.next_shape = self.get_random_shape()
        self.next_shape.move(3, 0)

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

    def drop_shape(self):
        while True:
            self.shape.move(0, 1)

            if self.is_shape_collide(self.shape):
                self.shape.move(0, -1)
                break

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

    def end_game(self):
        self.run = False


clock = pygame.time.Clock()

f1 = pygame.font.Font(PIXEL_FONT_PATH, 80)

animation = AnimatedSprite(load_image(ANIMATION_PATH), 17, 1, 194, 90)

while True:
    mode = start_screen()

    game_running = True

    field = Field(WIDTH // 2 - (field_width // 2 * CELL_SIZE), - 2 * CELL_SIZE, field_width, field_height + 2)

    field.start()

    while game_running:
        screen.fill(colors.BLACK)

        field.update()
        field.draw(screen)
        score = field.score
        score_text = f1.render(str(score), True, colors.WHITE)
        screen.blit(score_text, (((WIDTH - field_width * CELL_SIZE) / 2 - score_text.get_width()) / 2, HEIGHT * 0.3))

        tick = 0.7
        if mode == 1:
            time_left = 180 - time.time() + field.timer
            time_left_text = f1.render(f"{int(time_left // 60)}:{int(time_left % 60):02}", True, colors.WHITE)
            screen.blit(time_left_text,
                        (((WIDTH - field_width * CELL_SIZE) / 2 - time_left_text.get_width()) / 2, HEIGHT * 0.15))

            # Уровни сложности
            if time_left <= 30:
                level_text = f1.render('LEVEL 6', True, colors.WHITE)
                tick = 0.2
            elif time_left <= 60:
                level_text = f1.render('LEVEL 5', True, colors.WHITE)
                tick = 0.3
            elif time_left <= 90:
                level_text = f1.render('LEVEL 4', True, colors.WHITE)
                tick = 0.4
            elif time_left <= 120:
                level_text = f1.render('LEVEL 3', True, colors.WHITE)
                tick = 0.5
            elif time_left <= 150:
                level_text = f1.render('LEVEL 2', True, colors.WHITE)
                tick = 0.6
            else:
                level_text = f1.render('LEVEL 1', True, colors.WHITE)
                tick = 0.7
            screen.blit(level_text, (((WIDTH - field_width * CELL_SIZE) / 2 - level_text.get_width()) / 2, 0))

            if time_left <= 0:
                game_running = False

        pygame.draw.rect(screen, colors.WHITE, (WIDTH / 3 * 2 + (WIDTH / 3 - 150) / 2, HEIGHT / 2 - 150 / 2, 150, 150),
                         width=1)
        shape_preview = Shape(field.next_shape.shape, field.next_shape.color)
        shape_preview.move(WIDTH / 3 * 2 + (WIDTH / 3 - 150) / 2 + (
                150 - (max([i.rect.x for i in shape_preview.sprites()]) + CELL_SIZE)) / 2, HEIGHT / 2 - 150 / 2 + (
                                   150 - (max([i.rect.y for i in shape_preview.sprites()]) + CELL_SIZE)) / 2,
                           cell_based=False)
        shape_preview.draw(screen)

        menu_button = pygame.draw.rect(screen, colors.WHITE,
                                       (((WIDTH - field_width * CELL_SIZE) / 2 - 200) / 2, HEIGHT * 0.85, 200, 50))
        menu_text = f1.render('quit', True, colors.BLACK)
        screen.blit(menu_text,
                    (((WIDTH - field_width * CELL_SIZE) / 2 - 200) / 2 + ((200 - menu_text.get_width()) / 2),
                     HEIGHT * 0.85 - menu_text.get_height() * 0.25))

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
                field.set_tick(tick)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                field.drop_shape()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if menu_button.collidepoint(event.pos):
                        if mode == 1:
                            records_add(score)
                        game_running = False

        if field.tick != 0.05:
            field.set_tick(tick)

        if not field.run:
            game_running = False

        pygame.display.flip()
        clock.tick(FPS)

    if mode == 1:
        game_over_screen(score)
