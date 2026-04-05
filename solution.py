import sys

# Positional scores for tie-breaking: edges > center > corners
POS_SCORE = [
    [0, 2, 0],
    [2, 1, 2],
    [0, 2, 0],
]

# All 8 winning lines: 3 rows, 3 cols, 2 diagonals
LINES = [
    [(0, 0), (0, 1), (0, 2)],
    [(1, 0), (1, 1), (1, 2)],
    [(2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (2, 0)],
    [(0, 1), (1, 1), (2, 1)],
    [(0, 2), (1, 2), (2, 2)],
    [(0, 0), (1, 1), (2, 2)],
    [(0, 2), (1, 1), (2, 0)],
]


def check_winner(board):
    for line in LINES:
        a, b, c = line
        v = board[a[0]][a[1]]
        if v != '_' and v == board[b[0]][b[1]] == board[c[0]][c[1]]:
            return v
    return None


def get_empty_cells(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == '_']


def minimax(board, depth, is_maximizing, alpha, beta):
    winner = check_winner(board)
    if winner == 'X':
        return 10 - depth
    if winner == 'O':
        return depth - 10
    empties = get_empty_cells(board)
    if not empties:
        return 0

    if is_maximizing:
        best = float('-inf')
        for r, c in empties:
            board[r][c] = 'X'
            val = minimax(board, depth + 1, False, alpha, beta)
            board[r][c] = '_'
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = float('inf')
        for r, c in empties:
            board[r][c] = 'O'
            val = minimax(board, depth + 1, True, alpha, beta)
            board[r][c] = '_'
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def nextMove(player, board):
    is_maximizing = (player == 'X')
    best_score = float('-inf') if is_maximizing else float('inf')
    best_pos = -1
    best_row, best_col = -1, -1

    for r, c in get_empty_cells(board):
        board[r][c] = player
        score = minimax(board, 1, not is_maximizing, float('-inf'), float('inf'))
        board[r][c] = '_'

        pos = POS_SCORE[r][c]
        if is_maximizing:
            if score > best_score or (score == best_score and pos > best_pos):
                best_score, best_pos = score, pos
                best_row, best_col = r, c
        else:
            if score < best_score or (score == best_score and pos > best_pos):
                best_score, best_pos = score, pos
                best_row, best_col = r, c

    print(best_row, best_col)


data = sys.stdin.read().split()
player = data[0]
# Expand tokens character by character to handle both "_ X O" and "_ XO" formats
cells = [ch for token in data[1:] for ch in token]
board = [[cells[i * 3 + j] for j in range(3)] for i in range(3)]
nextMove(player, board)
