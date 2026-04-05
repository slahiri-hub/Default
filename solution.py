"""
Tic-Tac-Toe AI using Minimax with Alpha-Beta Pruning
-----------------------------------------------------
The Minimax algorithm is an adversarial search technique used in two-player
zero-sum games. It recursively explores all possible future game states,
assuming both players play optimally:
  - The maximiser (X) always picks the move with the highest score.
  - The minimiser (O) always picks the move with the lowest score.

Alpha-Beta Pruning optimises Minimax by eliminating branches that cannot
influence the final decision, significantly reducing the number of nodes
evaluated without changing the result.

Scoring:
  - X wins  ->  +( 10 - depth )   (earlier wins score higher)
  - O wins  ->  -( 10 - depth )   (earlier losses score lower)
  - Draw    ->   0
"""

import sys

# Positional tie-breaking scores used when two moves have equal Minimax scores.
# Center (score 2) are preferred over the corners (score 1) over edges (score 0).
POS_SCORE = [
    [1, 0, 1],
    [0, 2, 0],
    [1, 0, 1],
]

# All 8 possible winning lines: 3 rows, 3 columns, and 2 diagonals.
# Each line is a list of three (row, col) coordinates that form a winning sequence.
LINES = [
    [(0, 0), (0, 1), (0, 2)],  # row 0
    [(1, 0), (1, 1), (1, 2)],  # row 1
    [(2, 0), (2, 1), (2, 2)],  # row 2
    [(0, 0), (1, 0), (2, 0)],  # col 0
    [(0, 1), (1, 1), (2, 1)],  # col 1
    [(0, 2), (1, 2), (2, 2)],  # col 2
    [(0, 0), (1, 1), (2, 2)],  # main diagonal
    [(0, 2), (1, 1), (2, 0)],  # anti-diagonal
]


def check_winner(board):
    """
    Check all 8 winning lines for a completed sequence.
    Returns 'X' or 'O' if a winner is found, otherwise None.
    """
    for line in LINES:
        a, b, c = line
        v = board[a[0]][a[1]]
        if v != '_' and v == board[b[0]][b[1]] == board[c[0]][c[1]]:
            return v
    return None


def get_empty_cells(board):
    """Return a list of (row, col) positions for all unoccupied cells."""
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] == '_']


def minimax(board, depth, is_maximizing, alpha, beta):
    """
    Recursively evaluate the board using the Minimax algorithm with
    Alpha-Beta Pruning.

    Parameters:
        board          -- current 3x3 game state (mutated in-place and restored)
        depth          -- number of moves made from the root call
        is_maximizing  -- True if it is X's turn (maximiser), False for O (minimiser)
        alpha          -- best score the maximiser can guarantee so far
        beta           -- best score the minimiser can guarantee so far

    Returns:
        An integer score for the board state from X's perspective.

    Alpha-Beta Pruning:
        If beta <= alpha, the current branch cannot affect the result seen by
        the parent node, so remaining siblings are skipped (pruned).
    """
    # --- Base cases: terminal states ---
    winner = check_winner(board)
    if winner == 'X':
        # X wins; reward earlier wins with a higher score
        return 10 - depth
    if winner == 'O':
        # O wins; penalise earlier losses with a lower score
        return depth - 10

    empties = get_empty_cells(board)
    if not empties:
        # No winner and no moves left - the game is a draw
        return 0

    # --- Recursive case ---
    if is_maximizing:
        # X's turn: try every empty cell and keep the highest score
        best = float('-inf')
        for r, c in empties:
            board[r][c] = 'X'                                    # make move
            val = minimax(board, depth + 1, False, alpha, beta)  # recurse
            board[r][c] = '_'                                    # undo move
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break  # beta cut-off: minimiser would never allow this branch
        return best
    else:
        # O's turn: try every empty cell and keep the lowest score
        best = float('inf')
        for r, c in empties:
            board[r][c] = 'O'                                   # make move
            val = minimax(board, depth + 1, True, alpha, beta)  # recurse
            board[r][c] = '_'                                   # undo move
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break  # alpha cut-off: maximiser would never allow this branch
        return best


def nextMove(player, board):
    """
    Determine and print the optimal next move for the given player.

    For each empty cell, the move is simulated and scored with Minimax.
    The cell with the best Minimax score is selected. When scores are equal,
    POS_SCORE is used as a tie-breaker (edges > center > corners).

    Output: two space-separated integers representing the row and column
    of the chosen move (0-indexed, top-left is (0, 0)).
    """
    is_maximizing = (player == 'X')  # X maximises, O minimises

    best_score = float('-inf') if is_maximizing else float('inf')
    best_pos = -1          # positional tie-breaker score for the current best move
    best_row, best_col = -1, -1

    for r, c in get_empty_cells(board):
        board[r][c] = player  # simulate placing the player's mark

        # Evaluate the resulting position from the opponent's perspective
        score = minimax(board, 1, not is_maximizing, float('-inf'), float('inf'))

        board[r][c] = '_'     # undo the simulated move

        pos = POS_SCORE[r][c]

        # Update the best move if this cell has a strictly better Minimax score,
        # or an equal score but a more favourable board position.
        if is_maximizing:
            if score > best_score or (score == best_score and pos > best_pos):
                best_score, best_pos = score, pos
                best_row, best_col = r, c
        else:
            if score < best_score or (score == best_score and pos > best_pos):
                best_score, best_pos = score, pos
                best_row, best_col = r, c

    print(best_row, best_col)


# --- Input parsing ---
# Read all whitespace-separated tokens from stdin.
# Tokens are expanded character by character so both spaced ("_ X O") and
# compact ("_ XO") board formats are handled correctly.
data = sys.stdin.read().split()
player = data[0]
cells = [ch for token in data[1:] for ch in token]
board = [[cells[i * 3 + j] for j in range(3)] for i in range(3)]
nextMove(player, board)
