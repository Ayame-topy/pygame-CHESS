import pygame
from CONSTANTS import WIDTH, HEIGHT
from Game import Game


class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = self.init_screen()
        self.running = True
        self.game = Game()

    def init_screen(self):
        sc = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        return sc


    def main_loop(self):
        while self.running:
            if self.game.engine_play:
                self.game.get_engine_move()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self.game.on_click(pos)

            pygame.display.flip()

