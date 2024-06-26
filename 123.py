import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
FPS = 60

screen_width = 1000
screen_height = 750

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Ann')

font = pygame.font.SysFont(None, 100)
font_score = pygame.font.SysFont(None, 60)

tile_size = 50
game_over = 0
main_menu = True
level = 1
max_levels = 3
score = 0

bg_img = pygame.image.load('les.png')
restart_img = pygame.image.load('restart_btn.png')
start_img = pygame.image.load('start_btn.png')

#звуки
pygame.mixer.music.load('2.mp3')
pygame.mixer.music.play()
coin_fx = pygame.mixer.Sound('svet.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('prig.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('smert.wav')
game_over_fx.set_volume(0.5)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

def reset_level(level):
	player.reset(100, screen_height - 130)
	blob_group.empty()
	coin_group.empty()
	fire_group.empty()
	exit_group.empty()


	if path.exists(f'level{level}_data'):
		pickle_in = open(f'level{level}_data', 'rb')
		world_data = pickle.load(pickle_in)
	world = World(world_data)
	score_coin = Coin(tile_size // 2, tile_size // 2)
	coin_group.add(score_coin)
	return world
class Button():
	def __init__(self, x, y, image):
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.clicked = False

	def draw(self):
		action = False
		# позиция мыши
		pos = pygame.mouse.get_pos()

		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		# кнопк
		screen.blit(self.image, self.rect)

		return action

class Player():
	def __init__(self, x, y):
		self.reset(x, y)

	def update(self, game_over):
		dx = 0
		dy = 0
		walk_cooldown = 0

		if game_over == 0:

			#кнопки
			key = pygame.key.get_pressed()
			if key[pygame.K_SPACE] and self.jumped == False:
				jump_fx.play()
				self.vel_y = -15
				self.jumped = True
			if key[pygame.K_SPACE]==False:
				self.jumped = False
			if key[pygame.K_a]:
				dx -= 5
				self.counter += 1
				self.direction = -1
			if key[pygame.K_d]:
				dx += 5
				self.counter += 1
				self.direction = 1
			if key[pygame.K_a] == False and key[pygame.K_d] == False:
				self.counter = 0
				self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]

				#animat
				if self.counter > walk_cooldown:
					self.counter = 0
					self.index += 1
					if self.index >= len(self.images_right):
						self.index = 0
					if self.direction == 1:
						self.image = self.images_right[self.index]
					if self.direction == -1:
						self.image = self.images_left[self.index]

			#гравитация
			self.vel_y += 1
			if self.vel_y > 10:
				self.vel_y = 10
			dy += self.vel_y

			for tile in world.tile_list:   #столкновения с блоками
				if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.widht, self.height):
					dx = 0
				if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.widht, self.height):
					if self.vel_y < 0:
						dy = tile[1].bottom - self.rect.top
						self.vel_y = 0
					elif self.vel_y >= 0:
						dy = tile[1].top - self.rect.bottom
						self.vel_y = 0

			if pygame.sprite.spritecollide(self, blob_group, False):     #столкновение с врагами
				game_over = -1
				game_over_fx.play()
			if pygame.sprite.spritecollide(self, fire_group, False):     #столкновение с темнотой
				game_over = -1
				game_over_fx.play()
			if pygame.sprite.spritecollide(self, exit_group, False):
				game_over = 1

					#координаты игрока
			self.rect.x += dx
			self.rect.y += dy


		elif game_over == -1:
			self.image = self.dead_image
			if self.rect.y > 200:
				self.rect.y -= 5

		#персонаж на экране
		screen.blit(self.image, self.rect)

		return  game_over

	def reset(self, x, y):
		self.images_right = []
		self.images_left = []
		self.index = 0
		self.counter = 0
		for num in range(1, 5):
			img_right = pygame.image.load(f'guy{num}.png')
			img_right = pygame.transform.scale(img_right, (40, 80))
			img_left = pygame.transform.flip(img_right, True, False)
			self.images_right.append(img_right)
			self.images_left.append(img_left)
		self.dead_image = pygame.image.load('die.png')
		self.image = self.images_right[self.index]
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.widht = self.image.get_width()
		self.height = self.image.get_height()
		self.vel_y = 0
		self.jumped = False
		self.direction = 0
		self.num_jumps = 0
		self.max_jumps = 2

class World():
	def __init__(self, data):
		self.tile_list = []

		#load images
		dirt_img = pygame.image.load('plat.png')
		grass_img = pygame.image.load('grass.png')

		row_count = 0
		for row in data:
			col_count = 0
			for tile in row:
				if tile == 1:
					img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 2:
					img = pygame.transform.scale(grass_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 3:
					blob = Enemy(col_count * tile_size, row_count * tile_size + 16)
					blob_group.add( blob )
				if tile ==6:
					fire = Fire(col_count * tile_size, row_count * tile_size + 25)
					fire_group.add(fire)
				if tile == 7:
					coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
					coin_group.add(coin)
				if tile == 8:
					exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
					exit_group.add(exit)
				col_count += 1
			row_count += 1

	def draw(self):
		for tile in self.tile_list:
			screen.blit(tile[0], tile[1])

class Enemy(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('iskr.png')
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.move_direction = 1
		self.move_counter = 0

	def update(self):
		self.rect.x += self.move_direction    #движение слаймов
		self.move_counter += 1
		if self.move_counter > 100:
			self.move_direction *= -1
			self.move_counter = 0

class Fire(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('lava.png')
		self.image = pygame.transform.scale(img, (tile_size, tile_size//2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
class Coin(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('coin.png')
		self.image = pygame.transform.scale(img, (tile_size//2, tile_size//2))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)

class Exit (pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('exit.png')
		self.image = pygame.transform.scale(img, (tile_size, int(tile_size*3)))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y-100

player = Player(100, screen_height - 130)
fire_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
blob_group= pygame.sprite.Group()
exit_group = pygame.sprite.Group()
score_coin = Coin(tile_size-15 , tile_size-20)
coin_group.add(score_coin)
#zagruzk urovna
if path.exists(f'level{level}_data'):
	pickle_in = open(f'level{level}_data', 'rb')
	world_data = pickle.load(pickle_in)
world = World(world_data)
restart_button = Button(screen_width//2 - 180, screen_height// 2, restart_img)
start_button = Button(screen_width // 2 - 150, screen_height // 2, start_img)

run = True
while run:

	clock.tick(FPS)

	screen.blit(bg_img, (0, 0))
	if main_menu == True:
		if start_button.draw():
			main_menu = False
	else:
		world.draw()

		if game_over == 0:
			blob_group.update()
		if pygame.sprite.spritecollide(player, coin_group, True):
			score += 1
			coin_fx.play()
		draw_text('X ' + str(score), font_score, (255, 255, 255), tile_size, 20)
		blob_group.draw(screen)
		fire_group.draw(screen)
		coin_group.draw(screen)
		exit_group.draw(screen)
		game_over = player.update(game_over)
		#smert
		if game_over == -1:
			if restart_button.draw():
				player.reset(100, screen_height - 130)
				game_over = 0

		#pobeda
		if game_over == 1:
			# reset game and go to next level
			level += 1
			if level <= max_levels:
				# reset level
				world_data = []
				world = reset_level(level)
				game_over = 0
			else:
				if restart_button.draw():
					level = 1
					# reset level
					world_data = []
					world = reset_level(level)
					game_over = 0
					score = 0

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False

	pygame.display.update()

pygame.quit()