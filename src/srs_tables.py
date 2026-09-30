# srs_tables.py - Standard Super Rotation System (SRS) data
# Written cleanly and explicitly so any developer can easily follow along.

# Note on grid coordinates:
# x goes from 0 (left) to 9 (right).
# y goes from 0 (top of the board) to 23 (bottom of the board).
# Because y increases as we go DOWN, a kick that moves "UP" in Tetris Guideline
# subtracts from y (dy = -1), and a kick that moves "DOWN" adds to y (dy = +1).

# 4 rotation states for each of the 7 tetromino shapes.
# Each rotation state contains the (x_offset, y_offset) for the 4 mino blocks.
# State 0 is the initial spawn orientation.
# State 1 is 90 degrees clockwise (R).
# State 2 is 180 degrees (2).
# State 3 is 270 degrees clockwise / 90 degrees counter-clockwise (L).

TETROMINO_SHAPES = {
    'I': [
        # State 0 (horizontal)
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        # State 1 (vertical)
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        # State 2 (horizontal)
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        # State 3 (vertical)
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    'J': [
        # State 0
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        # State 1
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        # State 2
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        # State 3
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    'L': [
        # State 0
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        # State 1
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        # State 2
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        # State 3
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    'O': [
        # State 0, 1, 2, 3 are identical 2x2 square
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    'S': [
        # State 0
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        # State 1
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        # State 2
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        # State 3
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'T': [
        # State 0
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        # State 1
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        # State 2
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        # State 3
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'Z': [
        # State 0
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        # State 1
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        # State 2
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        # State 3
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
}

# Standard Guideline SRS Wall Kick Tables
# When rotating, the game checks 5 candidate positions (dx, dy).
# If the piece collides at test 1 (0, 0), it tries test 2, then test 3, etc.
# If none succeed, the rotation fails and the piece stays as it was.

# Wall kicks for J, L, S, T, Z pieces:
JLSTZ_KICK_TABLE = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}

# Wall kicks for the 'I' piece (it rotates inside a 4x4 bounding box):
I_KICK_TABLE = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}

def get_kicks(piece_type, current_rotation, target_rotation):
    """
    Returns the list of 5 kick offsets (dx, dy) to test for this rotation.
    If the piece is 'O', no kicks are needed since it's symmetric.
    """
    if piece_type == 'O':
        return [(0, 0)]
    
    transition = (current_rotation, target_rotation)
    if piece_type == 'I':
        return I_KICK_TABLE.get(transition, [(0, 0)])
    else:
        return JLSTZ_KICK_TABLE.get(transition, [(0, 0)])
