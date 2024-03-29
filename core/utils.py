def rotate_board_and_change_side(fen):
    def flip_case(c):
        return c.lower() if c.isupper() else c.upper()

    fen_parts = fen.swapcase().split(" ")

    # Rotate the board 180 degrees and change the case of the pieces
    rotated_board = "/".join(["".join(map(flip_case, row[::-1])) for row in reversed(fen_parts[0].split("/"))])

    # Change the side to move
    side_to_move = "w" if fen_parts[1] == "b" else "b"

    # Update the FEN
    new_fen = f"{rotated_board} {side_to_move} {fen_parts[2]} {fen_parts[3]} {fen_parts[4]} {fen_parts[5]}"
    return new_fen