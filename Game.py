import pygame
from CONSTANTS import ROW_SIZE, WHITE_ROWS_COLOR, BLACK_ROWS_COLOR, MOVES_ROUNDS_COLOR, END_SCREEN_COLOR
from Piece import *
from math import floor


class Game:
    def __init__(self):
        self.board, self.matrix, self.pieces_matrix, self.controlled_cases = self.init_board()
        set_board(self.matrix, self.pieces_matrix, self.controlled_cases)
        self.teams = [[], []]
        self.selected_piece = None
        self.playing = True
        self.screen = pygame.display.get_surface()
        self.sounds = {}
        self.init_sounds()
        self.init_pieces()
        self.update_board()
        self.playing_team = 1
        self.update_pieces()

    def init_board(self):
        # Create board
        board = pygame.Surface((ROW_SIZE*8, ROW_SIZE*8))
        colors = [WHITE_ROWS_COLOR, BLACK_ROWS_COLOR]
        for line in range(8):
            for column in range(8):
                pygame.draw.rect(board, colors[0], (column*ROW_SIZE, line*ROW_SIZE, ROW_SIZE, ROW_SIZE))

                colors.append(colors.pop(0))  # switch color
            colors.append(colors.pop(0))
        board_matrix = [[None for i in range(8)] for i in range(8)]
        pieces_matrix = [[None for i in range(8)] for i in range(8)]
        controlled_cases = [[[] for _ in range(8)] for _ in range(8)]

        return board, board_matrix, pieces_matrix, controlled_cases

    def init_pieces(self):
        pieces =  {
            Pawn: [(x, 1) for x in range(8)],
            Bishop: [(2, 0), (5, 0)],
            Horse: [(1, 0), (6, 0)],
            Rook: [(0, 0), (7, 0)],
            Queen: [(3, 0)],
            King: [(4, 0)]
        }
        for color in (0, 1):
            for piece in pieces:
                for pos in pieces[piece]:
                    if color == 1:
                        pos = pos[0], [7, 6][pos[1]]
                    p = piece(color, pos)
                    if type(p) is King:
                        p.set_castle_sound(self.sounds['castle'])
                    self.teams[color].append(p)

    def init_sounds(self):
        for sound in ('capture', 'move', 'castle', 'check', 'game_over'):
            self.sounds[sound] = pygame.mixer.Sound(file=fr'Sounds\{sound}.mp3')

    def play_sound(self, sound):
        pygame.mixer.pause()
        self.sounds[sound].play()

    def blit_board(self):
        self.screen.blit(self.board, (0, 0))

    def blit_pieces(self):
        for team in self.teams:
            for piece in team:
                x, y = piece.position
                self.screen.blit(piece.image, (x*ROW_SIZE, y*ROW_SIZE))

    def blit_piece_moves(self):
        if self.selected_piece is not None:
            for m in self.selected_piece.cases:
                x, y = m
                pygame.draw.circle(self.screen, MOVES_ROUNDS_COLOR, (x*ROW_SIZE+ROW_SIZE/2, y*ROW_SIZE+ROW_SIZE/2), ROW_SIZE/4)

    def update_board(self):
        self.blit_board()
        self.blit_pieces()
        self.blit_piece_moves()

    def on_click(self, pos):
        if self.playing:
            x, y = pos
            x = floor(x/ROW_SIZE)
            y = floor(y/ROW_SIZE)

            if self.selected_piece is None:
                if self.matrix[x][y] == self.playing_team:
                    self.selected_piece = self.pieces_matrix[x][y]
                    self.update_board()
            else:
                if (x, y) in self.selected_piece.cases:
                    if self.matrix[x][y] is not None:
                        self.teams[[1, 0][self.playing_team]].remove(self.pieces_matrix[x][y])
                        self.play_sound('capture')
                    else:
                        if type(self.selected_piece) is King:
                            if not self.selected_piece.castled:
                                self.play_sound('move')
                        else:
                            self.play_sound('move')
                    self.selected_piece.move((x, y))
                    if type(self.selected_piece) is Pawn:
                        self.check_passed_pawn(self.selected_piece)
                    self.change_playing_team()
                    self.selected_piece = None
                    self.update_board()
                    self.update_pieces()
                elif self.matrix[x][y] == self.playing_team:
                    self.selected_piece = self.pieces_matrix[x][y]
                    self.update_board()
                else:
                    self.selected_piece = None
                    self.update_board()
        else:
            self.__init__()

    def update_pieces(self):
        for c in self.controlled_cases:
            for case in c:
                case.clear()
        for team in self.teams:
            for piece in team:
                piece.update()
        self.on_check()

    def change_playing_team(self):
        self.playing_team = [1, 0][self.playing_team]

    def on_check(self):
        for piece in self.teams[self.playing_team]:
            if type(piece) is King:
                king = piece
                king.update()

        if len(king.attacking) > 0:
            if len(king.attacking) > 1:
                if len(king.cases) == 0:
                    self.win_game([1, 0][self.playing_team], 'Checkmate')
                    return
                for piece in self.teams[self.playing_team]:
                    piece.cases.clear()
                king.update()
            else:
                for attacker, move in king.attacking.items():
                    x, y = attacker.position
                    if attacker.long_range: lp = 7
                    else: lp = 1
                    moves = []
                    for i in range(lp):
                        m = (x+move[0]*i, y+move[1]*i)
                        if m != king.position:
                            moves.append(m)
                        else:
                            break

                for piece in self.teams[self.playing_team]:
                    if piece is not king:
                        piece.cases = list(set(piece.cases).intersection(moves))

                if sum(len(piece.cases) for piece in self.teams[self.playing_team]) == 0:
                    self.win_game([1, 0][self.playing_team], "Checkmate")
                    return
            king.attacking = {}
            self.play_sound('check')
        self.check_draw()

    def win_game(self, team, way):
        self.get_end_screen(f'{["Black", "White"][team]} won by {way}')

    def check_passed_pawn(self, pawn):
        if pawn.position[1] == (7, 0)[pawn.color]:
            new_piece = Queen(pawn.color, pawn.position)
            self.teams[pawn.color].append(new_piece)
            self.teams[pawn.color].remove(pawn)

    def check_draw(self):
        a, b = [len(team) for team in self.teams]
        if (a, b) == (1, 1):
            self.draw_game('Material failure')
            return
        elif (a, b) in ((1, 2), (2, 1), (2, 2)):
            draw = 0
            for team in self.teams:
                if len(team) == 1:
                    draw += 1
                    continue
                for piece in team:
                    if type(piece) in (Horse, Bishop):
                        draw += 1
            if draw == 2:
                self.draw_game('Material Failure')
                return
        if sum(len(piece.cases) for piece in self.teams[self.playing_team]) == 0:
            self.draw_game('Stalemate')

    def draw_game(self, way):
        self.get_end_screen(f'Game is Draw for {way}')

    def get_end_screen(self, message):
        self.playing = False
        font = pygame.font.SysFont('Arial', 50)
        screen = pygame.Surface((ROW_SIZE*4, ROW_SIZE*4))
        screen.fill(END_SCREEN_COLOR)
        text = font.render(message, True, (200, 200, 200))
        text = pygame.transform.scale(text, (screen.get_width(), (text.get_height()*screen.get_width()/text.get_width())))
        help = font.render('Click anywhere to restart a game', True, (200, 200, 200))
        help = pygame.transform.scale(help, (screen.get_width(), (help.get_height() * screen.get_width() / help.get_width())))
        screen.blit(text, (0, screen.get_height()/2 - text.get_height()/2))
        screen.blit(help, (screen.get_width()/2-help.get_width()/2, screen.get_height()-help.get_height()))
        self.play_sound('game_over')
        self.screen.blit(screen, (ROW_SIZE*2, ROW_SIZE*2))
