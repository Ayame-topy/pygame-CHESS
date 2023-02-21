import pygame
from CONSTANTS import ROW_SIZE

# Load images
images = pygame.image.load('ChessPiecesArray.png')


def get_piece_image(column, line):
    global images
    return pygame.transform.smoothscale(images.subsurface(60*column, 60*line, 60, 60), (ROW_SIZE, ROW_SIZE)).convert_alpha()


def get_horse_moves():
    moves = []
    for x in range(1, 3):
        y = 3-x
        moves.extend(((x, y), (x, -y), (-x, y), (-x, -y)))
    return tuple(moves)


# Set moves

DIAGONAL = (1, 1), (1, -1), (-1, 1), (-1, -1)
LATERAL = (1, 0), (-1, 0), (0, 1), (0, -1)
HORSE = get_horse_moves()

board = []
pieces_matrix = []
controlled_cases = []


def set_board(board_, pieces_matrix_, controlled_cases_):
    global board, pieces_matrix, controlled_cases
    board = board_
    pieces_matrix = pieces_matrix_
    controlled_cases = controlled_cases_


class Piece:
    def __init__(self, moves, image_c, color, position, long_range=False):
        self.image = get_piece_image(image_c, color)
        self.moves = moves
        self.get_moves = self.set_move_function(long_range)
        self.color = color
        self.position = position
        x, y = position
        board[x][y] = self.color
        pieces_matrix[x][y] = self
        self.cases = []
        self.long_range = long_range
        self.pinning = {}

    def __str__(self):
        return type(self).__name__ + ' ' + str(self.position)

    def set_move_function(self, long_range):
        if long_range:
            move = self.long_move
        else:
            move = self.short_move

        return move

    def pin_defender(self, piece, m):
        move = piece.position
        for i in range(8):
            move = move[0] + m[0], move[1] + m[1]
            if self.is_valid_move(move, control=False):
                p = pieces_matrix[move[0]][move[1]]
                if type(p) is King and p.color != self.color:
                    piece.pinning[self] = (-m[0], -m[1])
                    piece.update()
                    break
                elif p is not None:
                    break
            else:
                break

    def long_move(self):
        x, y = self.position
        for m in self.moves:
            for i in range(1, 8):
                move = x + m[0] * i, y + m[1] * i
                if self.is_valid_move(move):
                    self.cases.append(move)
                    if board[move[0]][move[1]] is not None:
                        piece = pieces_matrix[move[0]][move[1]]
                        if type(piece) is King:
                            piece.attacking[self] = m
                            for i in range(1, 7):
                                move = move[0] + m[0] * i, move[1] + m[1] * i
                                if self.is_valid_move(move):
                                    if board[move[0]][move[1]] is not None:
                                        self.add_controlled_case(move)
                                    else:
                                        break
                                else:
                                    break

                        else:
                            self.pin_defender(piece, m)
                        break
                else:
                    break

    def check_pin(self):
        if len(self.pinning) > 0:
            for pinner, move in self.pinning.items():
                pass
            if self.long_range:
                if move in self.moves:
                    cases = []
                    x, y = self.position
                    x_, y_ = move
                    for i in range(-7, 7):
                        x1 = x + x_*i
                        y1 = y + y_*i
                        if self.is_valid_move((x1, y1)):
                            if board[x1][y1] is None: cases.append((x1, y1))
                            else:
                                cases.append((x1, y1))
                                break
                    self.cases = cases
                else:
                    self.cases.clear()
            else:
                if move in self.moves:
                    self.cases.clear()
                    x, y = (self.position[0] + move[0], self.position[1] + move[1])
                    if board[x][y] is None:
                        self.cases.append((x, y))
                else:
                    self.cases.clear()

    def refresh_pins(self):
        x, y = self.position
        to_del = []
        for pinner, move in self.pinning.items():
            for i in range(1, 8):
                m_ = x - move[0]*i, y - move[1]*i
                if 0 <= m_[0] <= 7 and 0 <= m_[1] <= 7:
                    if board[m_[0]][m_[1]] == self.color and type(pieces_matrix[m_[0]][m_[1]]) is King:
                        break
                    elif pieces_matrix[m_[0]][m_[1]] is not None:
                        to_del.append(pinner)
                        break
                else:
                    to_del.append(pinner)
                    break
            x_, y_ = move
            for i in range(1, 9):
                x1 = x + x_ * i
                y1 = y + y_ * i
                if self.is_valid_move((x1, y1), control=False):
                    if pieces_matrix[x1][y1] is pinner:
                        break
                else:
                    to_del.append(pinner)
        for pin in set(to_del):
            del self.pinning[pin]

    def is_valid_move(self, move, control=True):
        x, y = move
        if 0 <= x <= 7 and 0 <= y <= 7:
            if control:
                self.add_controlled_case(move)
            if board[x][y] != self.color:
                return True
        return False

    def short_move(self):
        x, y = self.position
        for m in self.moves:
            move = x + m[0], y + m[1]
            if self.is_valid_move(move):
                self.cases.append(move)
                self.attack_king(move)

    def attack_king(self, move):
        if board[move[0]][move[1]] is not None:
            piece = pieces_matrix[move[0]][move[1]]
            if type(piece) is King:
                piece.attacking[self] = move

    def update(self):
        self.cases.clear()
        self.get_moves()
        self.refresh_pins()
        self.check_pin()

    def move(self, pos):
        x, y = self.position
        x_, y_ = pos

        board[x][y] = None
        board[x_][y_] = self.color

        pieces_matrix[x][y] = None
        pieces_matrix[x_][y_] = self

        self.position = pos

    def add_controlled_case(self, move):
        if self.color not in controlled_cases[move[0]][move[1]]:
            controlled_cases[move[0]][move[1]].append(self.color)


class Pawn(Piece):
    def __init__(self, color, pos):
        moves = ((0, (1, -1)[color]), )
        super().__init__(moves, 5, color, pos)
        self.get_moves = self.pawn_moves

    def pawn_moves(self):
        x_, y_ = self.moves[0]
        x, y = self.position
        move = x + x_, y + y_

        if self.is_valid_move(move, control=False):
            if board[move[0]][move[1]] is None:
                self.cases.append(move)
        if len(self.cases) != 0:
            x, y = self.cases[0]
            if board[x][y] is not None:  # Pawn can't eat in front
                self.cases.clear()
            elif self.position[1] == [1, 6][self.color]: # 2 cases move if first move
                if board[x][y+self.moves[0][1]] is None:
                    self.cases.append((x, y+self.moves[0][1]))
        for x in (-1, 1):  # Diagonal eat
            move = x + self.position[0], self.moves[0][1] + self.position[1]
            if self.is_valid_move(move):
                if board[move[0]][move[1]] is not None:
                    self.cases.append(move)
                    self.attack_king(move)

    def check_pin(self):
        if len(self.pinning) > 0:
            for pinner, move in self.pinning.items():
                pass
            if move in self.moves:
                self.get_moves()
                for c in self.cases:
                    if c[0] != self.position[0]:
                        self.cases.remove(c)
            elif pinner.position in self.cases:
                self.cases = [pinner.position]
            else:
                self.cases.clear()


class Bishop(Piece):
    def __init__(self, color, pos):
        super().__init__(DIAGONAL, 4, color, pos, long_range=True)


class Horse(Piece):
    def __init__(self, color, pos):
        super().__init__(HORSE, 3, color, pos)


class Rook(Piece):
    def __init__(self, color, pos):
        super().__init__(LATERAL, 2, color, pos, long_range=True)


class Queen(Piece):
    def __init__(self, color, pos):
        super().__init__(LATERAL+DIAGONAL, 0, color, pos, long_range=True)


class King(Piece):
    def __init__(self, color, pos, castle_sound=None):
        super().__init__(LATERAL+DIAGONAL, 1, color, pos)
        self.attacking = {}
        self.get_moves = self.king_moves
        self.castled = True
        self.castle_sound = None

    def set_castle_sound(self, sound: pygame.mixer.Sound):
        self.castle_sound = sound

    def move(self, pos):
        if self.castled:
            self.castled = False
            if abs(self.position[0]-pos[0]) == 2:
                self.castle(self.position[0]-pos[0])
        super().move(pos)

    def castle(self, side):
        x = 0 if side > 0 else 7
        mx = -1 if side > 0 else 1
        rock = pieces_matrix[x][self.position[1]]
        rock.move((self.position[0]+mx, self.position[1]))
        self.castle_sound.play()

    def king_moves(self):
        x, y = self.position
        for move in self.moves:
            mv = x + move[0], y + move[1]
            if self.is_valid_move(mv):
                if [1, 0][self.color] not in controlled_cases[mv[0]][mv[1]]:
                    self.cases.append(mv)
        if self.castled:
            for case, x in ((0, 1 ), (7, -1)):
                if type(pieces_matrix[case][self.position[1]]) is Rook:
                    rook = pieces_matrix[case][self.position[1]]
                    for i in range(1, 5):
                        x_ = rook.position[0]+x*i
                        if x_ == self.position[0]:
                            self.cases.append((self.position[0]-2*x, self.position[1]))
                            break
                        if board[x_][self.position[1]] is not None:
                            break
                        elif [1, 0][self.color] in controlled_cases[x_][self.position[1]]:
                            break
