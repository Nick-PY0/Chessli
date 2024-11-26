import os
import sys
import chess
import chess.engine
import chess.pgn
import PySimpleGUI as sg
import time
import random

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_FOLDER_PATH = os.path.join(BASE_DIR, 'engines')
IMAGE_FOLDER_PATH = os.path.join(BASE_DIR, 'images')
PGN_FOLDER_PATH = os.path.join(BASE_DIR, 'pgn')
HUMAN_VS_ENGINE_PATH = os.path.join(PGN_FOLDER_PATH, 'HumanVSEngine_PGNs')
ENGINE_VS_ENGINE_PATH = os.path.join(PGN_FOLDER_PATH, 'EngineVSEngine_PGNs')
ANALYSIS_PATH = os.path.join(PGN_FOLDER_PATH, 'Analysis_PGNs')

# Ensure PGN directories exist
os.makedirs(HUMAN_VS_ENGINE_PATH, exist_ok=True)
os.makedirs(ENGINE_VS_ENGINE_PATH, exist_ok=True)
os.makedirs(ANALYSIS_PATH, exist_ok=True)

class CustomEngine:
    def __init__(self, engine, difficulty):
        self.engine = engine
        self.difficulty = difficulty

    def play(self, board):
        if self.difficulty == "Super Duper Easy":
            # Always play a random move
            return random.choice(list(board.legal_moves))
        elif self.difficulty == "Easy":
            # 70% chance to play a random move
            if random.random() < 0.7:
                return random.choice(list(board.legal_moves))
            else:
                return self.engine.play(board, chess.engine.Limit(depth=1)).move
        elif self.difficulty == "Medium":
            # 50% chance to play a random move
            if random.random() < 0.5:
                return random.choice(list(board.legal_moves))
            else:
                return self.engine.play(board, chess.engine.Limit(depth=5)).move
        elif self.difficulty == "Hard":
            # Use engine's move but limit the depth
            return self.engine.play(board, chess.engine.Limit(depth=10)).move
        else:
            # 'Impossible' difficulty - use engine's best move
            return self.engine.play(board, chess.engine.Limit(time=0.1)).move

    def analyse(self, board, limit):
        # For hints, always use the best possible move
        return self.engine.analyse(board, limit)

    def quit(self):
        self.engine.quit()

def get_engines():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ENGINE_FOLDER_PATH = os.path.join(BASE_DIR, 'engines')
    engines = {
        'LC0': chess.engine.SimpleEngine.popen_uci(os.path.join(ENGINE_FOLDER_PATH, 'lc0-v0.30.0-windows-cpu-openblas', 'lc0.exe')),
        'Stockfish': chess.engine.SimpleEngine.popen_uci(os.path.join(ENGINE_FOLDER_PATH, 'stockfish', 'stockfish-windows-x86-64-avx2.exe')),
        'Komodo': chess.engine.SimpleEngine.popen_uci(os.path.join(ENGINE_FOLDER_PATH, 'komodo-14', 'Windows', 'komodo-14.1-64bit.exe')),
    }
    engines['LC0'].configure({'WeightsFile': os.path.join(ENGINE_FOLDER_PATH, 'lc0-v0.30.0-windows-cpu-openblas', 't1-256x10-distilled-swa-2432500.pb.gz')})
    return engines


def get_image_file(piece):
    if piece:
        piece_color = 'w' if piece.color == chess.WHITE else 'b'
        piece_name = piece.symbol().upper() if piece.color == chess.WHITE else piece.symbol().lower()
        return os.path.join(IMAGE_FOLDER_PATH, f"{piece_color}{piece_name}.png")
    return os.path.join(IMAGE_FOLDER_PATH, "empty.png")

def create_board_window(board, player_side='white', engine1_name=None, engine2_name=None):
    try:
        board_layout = []
        ranks = range(7, -1, -1) if player_side == 'white' else range(8)
        files = range(8) if player_side == 'white' else range(7, -1, -1)

        for rank in ranks:
            row = []
            for file in files:
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                image_file = get_image_file(piece)
                button_color = ('white', '#D18B47') if (rank + file) % 2 == 0 else ('black', '#FFCE9E')
                row.append(sg.Button('', image_filename=image_file, size=(64, 64), key=(rank, file), pad=(0, 0), button_color=button_color))
            board_layout.append(row)

        header_text = f"{engine1_name} (White) vs {engine2_name} (Black)" if engine1_name and engine2_name else "Chess Board"
        return sg.Window(header_text, board_layout, finalize=True)
    except Exception as e:
        sg.popup_error(f"Error creating board window: {e}")

def update_board_window(window, board, player_side='white', highlighted_squares=None):
    try:
        if highlighted_squares is None:
            highlighted_squares = set()
        ranks = range(7, -1, -1) if player_side == 'white' else range(8)
        files = range(8) if player_side == 'white' else range(7, -1, -1)
        for rank in ranks:
            for file in files:
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                image_file = get_image_file(piece)
                button_color = ('white', '#D18B47') if (rank + file) % 2 == 0 else ('black', '#FFCE9E')
                if square in highlighted_squares:
                    button_color = ('white', 'springgreen4')
                window[(rank, file)].update(image_filename=image_file, button_color=button_color)
    except Exception as e:
        sg.popup_error(f"Error updating board window: {e}")

def is_pawn_promotion(move, board):
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type == chess.PAWN:
        if (piece.color == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
           (piece.color == chess.BLACK and chess.square_rank(move.to_square) == 0):
            return True
    return False

def pawn_promotion(color):
    promotion_pieces = {'Queen': chess.QUEEN, 'Rook': chess.ROOK, 'Bishop': chess.BISHOP, 'Knight': chess.KNIGHT}
    layout = [
        [sg.Text("Choose piece for promotion:")],
        [sg.Button(piece, key=piece) for piece in promotion_pieces.keys()],
        [sg.Button("Cancel", key="Cancel")]
    ]
    window = sg.Window("Pawn Promotion", layout, modal=True)
    event, _ = window.read()
    window.close()
    if event in promotion_pieces:
        return promotion_pieces[event]
    else:
        return None

def save_game(game, default_path, allow_save=True):
    try:
        if not allow_save:
            sg.popup("Game modifications prevent saving to PGN.")
            return

        layout = [
            [sg.Text("Do you want to save this game?")],
            [sg.Button("Yes"), sg.Button("No")]
        ]
        save_window = sg.Window("Save Game", layout)
        event, _ = save_window.read()
        save_window.close()

        if event == "Yes":
            file_path = sg.popup_get_file("Save PGN file", save_as=True, default_extension=".pgn",
                                          initial_folder=default_path, file_types=(("PGN Files", "*.pgn"),))
            if file_path:
                with open(file_path, 'w') as pgn_file:
                    try:
                        exporter = chess.pgn.FileExporter(pgn_file)
                        game.accept(exporter)
                        sg.popup(f"Game saved to {file_path}")
                    except Exception as e:
                        sg.popup_error(f"Failed to save game: {e}")
    except Exception as e:
        sg.popup_error(f"Error during game saving: {e}")

def select_engine(engines):
    try:
        difficulty_levels = [
            "Super Duper Easy",
            "Easy",
            "Medium",
            "Hard",
            "Impossible"
        ]

        layout = [
            [sg.Text('Select an engine for the game')],
            [sg.Listbox(list(engines.keys()), size=(20, len(engines)), key='Engine', select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text("Select Difficulty:"), sg.Combo(difficulty_levels, key='Difficulty', default_value='Medium')],
            [sg.Button('Confirm', key='Confirm')]
        ]
        selection_window = sg.Window('Engine Selection', layout)
        while True:
            event, values = selection_window.read()
            if event in (sg.WIN_CLOSED, 'Confirm'):
                break
        selection_window.close()
        if event == sg.WIN_CLOSED or not values['Engine']:
            return None, None
        selected_engine = values['Engine'][0]
        selected_difficulty = values['Difficulty']
        return selected_engine, selected_difficulty
    except Exception as e:
        sg.popup_error(f"Error during engine selection: {e}")
        return None, None

def select_two_engines(engines):
    try:
        difficulty_levels = [
            "Super Duper Easy",
            "Easy",
            "Medium",
            "Hard",
            "Impossible"
        ]

        layout = [
            [sg.Text('Select two engines for a game')],
            [sg.Text('Engine 1:')],
            [sg.Listbox(list(engines.keys()), size=(20, len(engines)), key='Engine1', select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text("Select Difficulty for Engine 1:"), sg.Combo(difficulty_levels, key='Difficulty1', default_value='Medium')],
            [sg.Text('Engine 2:')],
            [sg.Listbox(list(engines.keys()), size=(20, len(engines)), key='Engine2', select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text("Select Difficulty for Engine 2:"), sg.Combo(difficulty_levels, key='Difficulty2', default_value='Medium')],
            [sg.Button('Start Game', key='StartGame')]
        ]
        selection_window = sg.Window('Engine Selection', layout)
        while True:
            event, values = selection_window.read()
            if event in (sg.WIN_CLOSED, 'StartGame'):
                break
        selection_window.close()
        if event == sg.WIN_CLOSED or not values['Engine1'] or not values['Engine2']:
            return None, None, None, None
        engine1_name = values['Engine1'][0]
        engine2_name = values['Engine2'][0]
        difficulty1 = values['Difficulty1']
        difficulty2 = values['Difficulty2']
        return engine1_name, engine2_name, difficulty1, difficulty2
    except Exception as e:
        sg.popup_error(f"Error during engine selection for two engines: {e}")
        return None, None, None, None

def select_side():
    try:
        layout = [[sg.Text("Select your side:")],
                  [sg.Listbox(["white", "black"], size=(10, 2), key="Side")],
                  [sg.Button("Confirm", key="Confirm")]]
        side_window = sg.Window("Select Side", layout)
        while True:
            event, values = side_window.read()
            if event in (sg.WIN_CLOSED, "Confirm"):
                break
        side_window.close()
        return values["Side"][0] if event != sg.WIN_CLOSED and values["Side"] else None
    except Exception as e:
        sg.popup_error(f"Error during side selection: {e}")
        return None

def select_analysis_mode():
    try:
        layout = [
            [sg.Text("Select analysis mode:")],
            [sg.Button("Load FEN", key="LoadFEN"), sg.Button("Load PGN", key="LoadPGN"),
             sg.Button("Standard", key="Standard"), sg.Button("Random", key="Random"), sg.Button("Clear Board", key="Clear")],
            [sg.Button("Cancel", key="Cancel")]
        ]
        mode_window = sg.Window("Select Analysis Mode", layout)
        event, _ = mode_window.read()
        mode_window.close()
        return event
    except Exception as e:
        sg.popup_error(f"Error during analysis mode selection: {e}")
        return None

def generate_random_position():
    import random
    board = chess.Board()
    moves = list(board.legal_moves)
    for _ in range(random.randint(5, 20)):
        move = random.choice(moves)
        board.push(move)
        moves = list(board.legal_moves)
        if board.is_game_over():
            break
    return board

def enforce_single_king_per_side(board):
    white_kings = list(board.pieces(chess.KING, chess.WHITE))
    black_kings = list(board.pieces(chess.KING, chess.BLACK))

    if len(white_kings) != 1 or len(black_kings) != 1:
        sg.popup("Invalid number of kings detected. There must be exactly one king per side.")
        # Remove extra kings or add missing kings
        # Remove all kings
        for square in white_kings:
            board.remove_piece_at(square)
        for square in black_kings:
            board.remove_piece_at(square)
        # Add one king per side at default positions if vacant
        if not board.piece_at(chess.E1):
            board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
        if not board.piece_at(chess.E8):
            board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
        sg.popup("Kings have been reset to their default positions.")

def has_both_kings(board):
    return board.king(chess.WHITE) is not None and board.king(chess.BLACK) is not None

def play_game(human_side, engine, engines, main_window, save_path, game_number, difficulty, is_analysis_mode=False):
    import time
    board = chess.Board()
    game = chess.pgn.Game()
    current_node = game
    move_history = []
    current_move_index = 0
    player_color = chess.WHITE if human_side == 'white' else chess.BLACK

    custom_engine = CustomEngine(engine, difficulty)

    board_window = create_board_window(board, player_side=human_side)
    control_layout = [
        [sg.Button("Hint", key="-HINT-", size=(12, 1)), sg.Button("Undo", key="-UNDO-", size=(12, 1)),
         sg.Button("Redo", key="-REDO-", size=(12, 1)), sg.Button("Resign", key="-RESIGN-", size=(12, 1))],
        [sg.Button("Start", key="-START-", size=(12, 1)), sg.Button("Backward", key="-BACKWARD-", size=(12, 1)),
         sg.Button("Forward", key="-FORWARD-", size=(12, 1)), sg.Button("End", key="-END-", size=(12, 1))],
        [sg.Button("AutoPlay: Off", key="-AUTOPLAY-", size=(12, 1)), sg.Text("Speed:"),
         sg.Slider(range=(1, 10), orientation='h', size=(20, 15), key="-SPEED-", default_value=5)],
        [sg.Button("Summon Piece", key="-SUMMON-", size=(12, 1)),
         sg.Button("Reset Board", key="-RESET-", size=(12, 1))],
        [sg.Text("FEN:"), sg.InputText(key="-FEN-", size=(50, 1)), sg.Button("Copy FEN", key="-COPY-FEN-", size=(12, 1))],
        [sg.Listbox(values=[], size=(60, 10), key='-MOVE-LIST-')]  # Move List to display moves
    ]
    control_window = sg.Window("Game Controls", control_layout, finalize=True)

    selected_square = None
    autoplay = False
    autoplay_speed = 5
    setup_mode = False

    game_over = False

    def update_board(highlight_squares=None):
        if highlight_squares is None:
            highlight_squares = set()
        update_board_window(board_window, board, player_side=human_side, highlighted_squares=highlight_squares)
        control_window["-FEN-"].update(board.fen())
        move_list = []
        node = game
        while node.variations:
            node = node.variations[0]
            move_list.append(node.move.uci())
        control_window['-MOVE-LIST-'].update(move_list)

    def make_move(move, is_engine_move=False):
        nonlocal current_node, current_move_index, game_over
        if move is None:
            sg.popup_error("Move is not properly assigned. Please try again.")
            return False

        # Check if the move would capture a king
        target_piece = board.piece_at(move.to_square)
        if target_piece and target_piece.piece_type == chess.KING:
            sg.popup("Cannot capture the king. This move results in checkmate.")
            # Declare checkmate
            result = "1-0" if board.turn == chess.WHITE else "0-1"
            game.headers["Result"] = result
            game_over = True
            update_board()
            return False

        try:
            if current_move_index < len(move_history):
                move_history[:] = move_history[:current_move_index]
                current_node.variations = []
                current_node.comment = ""

            board.push(move)
            move_history.append(move)
            current_move_index += 1
            new_node = current_node.add_variation(move)
            current_node = new_node
            update_board(highlight_squares={move.from_square, move.to_square})

            # Check for game over
            if board.is_checkmate():
                result = "1-0" if board.turn == chess.BLACK else "0-1"
                sg.popup(f"Checkmate! {'White' if result == '1-0' else 'Black'} wins.")
                game.headers["Result"] = result
                game_over = True
            elif board.is_stalemate():
                sg.popup("Stalemate! The game is a draw.")
                game.headers["Result"] = "1/2-1/2"
                game_over = True

            return True
        except Exception as e:
            sg.popup_error(f"Error making move: {e}")
            return False

    def undo_move():
        nonlocal current_node, current_move_index
        if current_move_index > 0 and current_node.parent is not None:
            board.pop()
            current_node = current_node.parent
            current_move_index -= 1
            move_history.pop()
            update_board()

    def redo_move():
        nonlocal current_node, current_move_index
        if current_node.variations and current_move_index < len(move_history) + 1:
            move = current_node.variations[0].move
            if is_pawn_promotion(move, board) and move.promotion is None:
                move.promotion = chess.QUEEN
            board.push(move)
            current_node = current_node.variations[0]
            current_move_index += 1
            move_history.append(move)
            update_board()

    def provide_hint():
        try:
            if not has_both_kings(board):
                sg.popup("Cannot provide a hint on an invalid board position.")
                return
            result = custom_engine.analyse(board, chess.engine.Limit(time=0.1))
            if 'pv' in result and len(result['pv']) > 0:
                best_move = result['pv'][0]
                update_board(highlight_squares={best_move.from_square, best_move.to_square})
            else:
                sg.popup_error("Engine did not return a valid principal variation (PV).")
        except Exception as e:
            sg.popup_error(f"Error providing hint: {e}")

    def summon_piece():
        nonlocal current_node, move_history, current_move_index
        piece_symbols = ['P', 'N', 'B', 'R', 'Q', 'K']
        colors = {'White': chess.WHITE, 'Black': chess.BLACK}

        color_event, _ = sg.Window("Select Color", [
            [sg.Text("Select piece color:")],
            [sg.Button("White"), sg.Button("Black")],
            [sg.Button("Cancel")]
        ], modal=True).read(close=True)

        if color_event in colors:
            piece_color = colors[color_event]
        else:
            sg.popup("Summoning piece cancelled.")
            return

        piece_event, _ = sg.Window("Summon Piece", [
            [sg.Text("Select a piece to summon:")],
            [sg.Button(symbol) for symbol in piece_symbols],
            [sg.Button("Cancel")]
        ], modal=True).read(close=True)

        if piece_event in piece_symbols:
            piece_type_dict = {'P': chess.PAWN, 'N': chess.KNIGHT, 'B': chess.BISHOP,
                               'R': chess.ROOK, 'Q': chess.QUEEN, 'K': chess.KING}
            summoning_piece = chess.Piece(piece_type_dict[piece_event], piece_color)
            sg.popup("Now click on the board to place the piece.")
        else:
            sg.popup("Summoning piece cancelled.")
            return

        while True:
            board_event, _ = board_window.read(timeout=100)

            if board_event == sg.WIN_CLOSED:
                break

            if isinstance(board_event, tuple) and len(board_event) == 2:
                rank, file = board_event
                square = chess.square(file, rank)

                # Prevent replacing a king
                existing_piece = board.piece_at(square)
                if existing_piece and existing_piece.piece_type == chess.KING:
                    sg.popup("Cannot replace a king. Please choose another square.")
                    continue

                # Place or replace the piece at the selected square
                board.set_piece_at(square, summoning_piece)
                enforce_single_king_per_side(board)
                current_node = current_node.add_variation(chess.Move.null())
                move_history.append(chess.Move.null())
                current_move_index += 1
                update_board()
                sg.popup("Piece placed successfully!")
                break

    def clear_the_board():
        nonlocal current_node, move_history, current_move_index, setup_mode
        # Remove all pieces except kings
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                board.remove_piece_at(square)
        setup_mode = True
        sg.popup("Board cleared. You are now in setup mode. Place pieces or reset the board.")
        current_node = current_node.add_variation(chess.Move.null())
        current_move_index += 1
        move_history.append(chess.Move.null())
        update_board()

    update_board()

    if board.turn != player_color and has_both_kings(board):
        try:
            result_move = custom_engine.play(board)
            make_move(result_move, is_engine_move=True)
        except Exception as e:
            sg.popup_error(f"Engine error: {e}")

    while True:
        if game_over:
            result = game.headers.get("Result", "1/2-1/2")
            winner = "White" if result == "1-0" else "Black" if result == "0-1" else "Draw"
            sg.popup(f'Game over. Result: {result}. Winner: {winner}\nDifficulty: {difficulty}')
            break

        window, event, values = sg.read_all_windows(timeout=100)

        if window == control_window and (event == sg.WIN_CLOSED or event == "-RESIGN-"):
            game.headers["Result"] = board.result(claim_draw=True)
            break

        if window == board_window and event == sg.WIN_CLOSED:
            break

        if window == board_window:
            if isinstance(event, tuple):
                rank, file = event
                square = chess.square(file, rank)

                if selected_square is None:
                    piece = board.piece_at(square)
                    if piece and (piece.color == board.turn == player_color or setup_mode):
                        selected_square = square
                        try:
                            legal_moves = [move for move in board.legal_moves if move.from_square == selected_square]
                            update_board(highlight_squares={move.to_square for move in legal_moves})
                        except Exception as e:
                            sg.popup_error(f"Error fetching legal moves: {e}")
                            selected_square = None
                    else:
                        selected_square = None
                        update_board()
                else:
                    if setup_mode:
                        # Move or place piece in setup mode
                        piece = board.piece_at(selected_square)
                        if piece and piece.piece_type == chess.KING:
                            sg.popup("Cannot move the king in setup mode.")
                            selected_square = None
                            update_board()
                            continue
                        board.remove_piece_at(selected_square)
                        board.set_piece_at(square, piece)
                        enforce_single_king_per_side(board)
                        current_node = current_node.add_variation(chess.Move.null())
                        current_move_index += 1
                        move_history.append(chess.Move.null())
                        selected_square = None
                        update_board()
                    else:
                        try:
                            legal_moves = [move for move in board.legal_moves if move.from_square == selected_square and move.to_square == square]
                        except Exception as e:
                            sg.popup_error(f"Error generating legal moves: {e}")
                            selected_square = None
                            update_board()
                            continue

                        if not legal_moves:
                            selected_square = None
                            update_board()
                        else:
                            if len(legal_moves) == 1:
                                move = legal_moves[0]
                                if make_move(move):
                                    selected_square = None
                                    if not board.is_game_over() and board.turn != player_color and has_both_kings(board):
                                        try:
                                            result_move = custom_engine.play(board)
                                            make_move(result_move, is_engine_move=True)
                                        except Exception as e:
                                            sg.popup_error(f"Engine error: {e}")
                                else:
                                    selected_square = None
                                    update_board()
                            else:
                                if is_pawn_promotion(legal_moves[0], board):
                                    promotion_piece = pawn_promotion('w' if board.turn == chess.WHITE else 'b')
                                    if promotion_piece is None:
                                        selected_square = None
                                        update_board()
                                    else:
                                        move = chess.Move(selected_square, square, promotion=promotion_piece)
                                        if move in legal_moves:
                                            if make_move(move):
                                                selected_square = None
                                                if not board.is_game_over() and board.turn != player_color and has_both_kings(board):
                                                    try:
                                                        result_move = custom_engine.play(board)
                                                        make_move(result_move, is_engine_move=True)
                                                    except Exception as e:
                                                        sg.popup_error(f"Engine error: {e}")
                                            else:
                                                selected_square = None
                                                update_board()
                                        else:
                                            sg.popup_error("Invalid promotion move.")
                                            selected_square = None
                                            update_board()
                                else:
                                    selected_square = None
                                    update_board()

        elif window == control_window:
            if event == "-HINT-":
                provide_hint()
            elif event == "-UNDO-":
                undo_move()
            elif event == "-REDO-":
                redo_move()
            elif event == "-START-":
                while current_move_index > 0:
                    undo_move()
            elif event == "-END-":
                while current_node.variations:
                    redo_move()
            elif event == "-BACKWARD-":
                undo_move()
            elif event == "-FORWARD-":
                redo_move()
            elif event == "-AUTOPLAY-":
                autoplay = not autoplay
                control_window["-AUTOPLAY-"].update(f"AutoPlay: {'On' if autoplay else 'Off'}")
            elif event == "-SPEED-":
                autoplay_speed = values["-SPEED-"]
            elif event == "-SUMMON-":
                summon_piece()
            elif event == "-RESET-":
                board.reset()
                game = chess.pgn.Game()
                current_node = game
                move_history.clear()
                current_move_index = 0
                selected_square = None
                setup_mode = False
                enforce_single_king_per_side(board)
                update_board()
            elif event == "-COPY-FEN-":
                sg.clipboard_set(board.fen())
                sg.popup("FEN copied to clipboard!")
            elif event == "-FEN-":
                fen_input = values["-FEN-"]
                try:
                    board.set_fen(fen_input)
                    enforce_single_king_per_side(board)
                    game = chess.pgn.Game()
                    current_node = game
                    move_history.clear()
                    current_move_index = 0
                    selected_square = None
                    setup_mode = False
                    update_board()
                except ValueError as e:
                    sg.popup_error(f"Invalid FEN string: {e}")

        if autoplay and not board.is_game_over() and not game_over and has_both_kings(board):
            if board.turn == player_color:
                try:
                    result_move = custom_engine.play(board)
                    make_move(result_move)
                except Exception as e:
                    sg.popup_error(f"Engine error: {e}")
            else:
                try:
                    result_move = custom_engine.play(board)
                    make_move(result_move, is_engine_move=True)
                except Exception as e:
                    sg.popup_error(f"Engine error: {e}")
            time.sleep(1.0 / autoplay_speed)

    board_window.close()
    control_window.close()
    save_game(game, save_path, allow_save=not is_analysis_mode)
    return board.fen()

def engine_vs_engine_game(engine1, engine2, main_window, save_path, game_number, engine1_name, engine2_name):
    """
    Handles playing a game between two engines.
    """
    import threading
    import time

    try:
        board = chess.Board()
        enforce_single_king_per_side(board)
        game = chess.pgn.Game()
        current_node = game
        move_history = []

        # Create the board window
        board_window = create_board_window(board, player_side='white', engine1_name=engine1_name, engine2_name=engine2_name)

        # Control window layout
        control_layout = [
            [sg.Button("Pause", key="-PAUSE-"), sg.Button("Resume", key="-RESUME-", disabled=True), sg.Button("Stop", key="-STOP-")],
            [sg.Button("<<", key="-START-"), sg.Button("<", key="-BACKWARD-"), sg.Button(">", key="-FORWARD-"), sg.Button(">>", key="-END-")],
            [sg.Listbox(values=[], size=(60, 10), key='-MOVE-LIST-')]  # Move List to display moves
        ]
        control_window = sg.Window("Engine vs Engine Controls", control_layout, finalize=True)

        paused = False
        game_active = True
        move_event = threading.Event()

        def update_board():
            update_board_window(board_window, board, player_side='white')
            # Update move list
            move_list = []
            node = game
            while node.variations:
                node = node.variations[0]
                move_list.append(node.move.uci())
            control_window['-MOVE-LIST-'].update(move_list)

        def engine_move():
            nonlocal current_node, board, game_active, move_history
            current_engine = engine1  # Start with engine1
            while game_active and not board.is_game_over():
                if paused:
                    move_event.wait()
                try:
                    # Check if both kings are present
                    if not has_both_kings(board):
                        sg.popup("Invalid board state detected. Restoring kings.")
                        enforce_single_king_per_side(board)
                        update_board()

                    # Set a time limit for engine moves
                    result = current_engine.play(board)
                    move = result

                    # Check if the move would capture a king
                    target_piece = board.piece_at(move.to_square)
                    if target_piece and target_piece.piece_type == chess.KING:
                        sg.popup("Cannot capture the king. This move results in checkmate.")
                        # Declare checkmate
                        result = "1-0" if board.turn == chess.WHITE else "0-1"
                        game.headers["Result"] = result
                        game_active = False
                        break

                    # Handle pawn promotion
                    if is_pawn_promotion(move, board) and move.promotion is None:
                        move.promotion = chess.QUEEN  # Default promotion to Queen

                    # Apply the move
                    board.push(move)
                    move_history.append(move)
                    new_node = current_node.add_variation(move)
                    current_node = new_node

                    # Update the board and GUI
                    update_board()
                    time.sleep(0.1)  # Small delay to update GUI

                    # Check for game over
                    if board.is_checkmate():
                        result = "1-0" if board.turn == chess.BLACK else "0-1"
                        sg.popup(f"Checkmate! {'White' if result == '1-0' else 'Black'} wins.")
                        game.headers["Result"] = result
                        game_active = False
                        break
                    elif board.is_stalemate():
                        sg.popup("Stalemate! The game is a draw.")
                        game.headers["Result"] = "1/2-1/2"
                        game_active = False
                        break

                    # Switch engines
                    current_engine = engine2 if current_engine == engine1 else engine1

                except Exception as e:
                    sg.popup_error(f"Engine error: {e}")
                    game_active = False
                    break

        # Start the engine vs engine game in a separate thread
        game_thread = threading.Thread(target=engine_move, daemon=True)
        game_thread.start()

        while True:
            event, _ = control_window.read(timeout=100)

            if event == sg.WIN_CLOSED or event == "-STOP-":
                game_active = False
                break
            elif event == "-PAUSE-":
                paused = True
                control_window["-PAUSE-"].update(disabled=True)
                control_window["-RESUME-"].update(disabled=False)
            elif event == "-RESUME-":
                paused = False
                move_event.set()
                control_window["-PAUSE-"].update(disabled=False)
                control_window["-RESUME-"].update(disabled=True)
                move_event.clear()
            elif event == "-FORWARD-" and current_node.variations:
                current_node = current_node.variations[0]
                board = current_node.board()
                update_board()
            elif event == "-BACKWARD-" and current_node.parent:
                current_node = current_node.parent
                board = current_node.board()
                update_board()
            elif event == "-START-":
                current_node = game
                board = current_node.board()
                update_board()
            elif event == "-END-":
                while current_node.variations:
                    current_node = current_node.variations[0]
                board = current_node.board()
                update_board()

        # Wait for the game thread to finish
        game_thread.join()

        board_window.close()
        control_window.close()

        save_game(game, save_path)
        return board.fen()
    except Exception as e:
        sg.popup_error(f"Error during engine vs engine game: {e}")

def gui_to_board_coordinates(gui_rank, gui_file, player_side):
    if player_side == 'white':
        rank = 7 - gui_rank
        file = gui_file
    else:
        rank = gui_rank
        file = 7 - gui_file
    return rank, file

def has_both_kings(board):
    return board.king(chess.WHITE) is not None and board.king(chess.BLACK) is not None

def analyze_position(fen_or_pgn_input, main_window, engines, analysis_path, game_number, mode='Standard'):
    import io
    import time
    import os
    import chess
    import chess.pgn
    import chess.engine
    import PySimpleGUI as sg

    try:
        # Initialize variables
        game = chess.pgn.Game()
        current_node = game
        autoplay = False
        autoplay_speed = 5
        player_side = 'white'
        selected_engine = 'Stockfish'  # Default engine
        selected_square = None
        last_autoplay_time = time.time()
        move_history = []
        current_move_index = 0
        allow_illegal_moves = False
        game_over = False  # Flag to control game over state

        # Handle different modes and input
        if mode == 'Random':
            board = generate_random_position()
            game.setup(board)
            current_node = game
        elif fen_or_pgn_input:
            # Attempt to interpret input as FEN
            try:
                board = chess.Board(fen_or_pgn_input)
                game.setup(board)
                current_node = game
            except ValueError:
                # Not a valid FEN, try to read as PGN file
                if os.path.isfile(fen_or_pgn_input):
                    try:
                        with open(fen_or_pgn_input, 'r') as pgn_file:
                            game = chess.pgn.read_game(pgn_file)
                            if game is None:
                                raise ValueError("Failed to read PGN file.")
                            current_node = game
                            board = current_node.board()
                    except Exception as e:
                        sg.popup_error(f"Error reading PGN file: {e}")
                        return
                else:
                    # Try to interpret input as PGN content
                    try:
                        pgn_io = io.StringIO(fen_or_pgn_input)
                        game = chess.pgn.read_game(pgn_io)
                        if game is None:
                            raise ValueError("Failed to parse PGN text.")
                        current_node = game
                        board = current_node.board()
                    except Exception as e:
                        sg.popup_error(f"Invalid PGN input: {e}")
                        return
        else:
            # Default to starting position
            board = chess.Board()
            game.setup(board)
            current_node = game

        # Helper functions
        def is_pawn_promotion(move, board):
            piece = board.piece_at(move.from_square)
            if piece is None or piece.piece_type != chess.PAWN:
                return False
            to_rank = chess.square_rank(move.to_square)
            return (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0)

        def pawn_promotion(color):
            promotion_pieces = ['Queen', 'Rook', 'Bishop', 'Knight']
            layout = [
                [sg.Text('Promote pawn to:')],
                [sg.Button(piece) for piece in promotion_pieces],
                [sg.Button('Cancel')]
            ]
            window = sg.Window('Pawn Promotion', layout)
            event, _ = window.read()
            window.close()
            if event in promotion_pieces:
                piece_dict = {'Queen': chess.QUEEN, 'Rook': chess.ROOK, 'Bishop': chess.BISHOP, 'Knight': chess.KNIGHT}
                return piece_dict[event]
            else:
                return None

        def has_both_kings(board):
            return board.king(chess.WHITE) is not None and board.king(chess.BLACK) is not None

        def enforce_single_king_per_side(board):
            white_kings = list(board.pieces(chess.KING, chess.WHITE))
            black_kings = list(board.pieces(chess.KING, chess.BLACK))

            if len(white_kings) != 1 or len(black_kings) != 1:
                sg.popup("Invalid number of kings detected. There must be exactly one king per side.")
                # Remove extra kings
                for square in white_kings[1:]:
                    board.remove_piece_at(square)
                for square in black_kings[1:]:
                    board.remove_piece_at(square)
                # Add missing kings at default positions
                if not white_kings:
                    board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
                if not black_kings:
                    board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
                sg.popup("Kings have been reset to their default positions.")

        # Create the board window
        board_window = create_board_window(board, player_side=player_side)
        if not board_window:
            return

        # Control layout
        control_layout = [
            [
                sg.Text("Engine:"),
                sg.Combo(list(engines.keys()), default_value=selected_engine, key='-ENGINE-', enable_events=True),
                sg.Button("Analyze", key="-ANALYZE-"),
                sg.Button("Hint", key="-HINT-")
            ],
            [
                sg.Button("<<", key="-START-"),
                sg.Button("<", key="-PREV-"),
                sg.Button(">", key="-NEXT-"),
                sg.Button(">>", key="-END-"),
                sg.Button("Autoplay: Off", key="-AUTOPLAY-"),
                sg.Text("Speed:"),
                sg.Slider(range=(1, 10), default_value=5, orientation='h', size=(10, 15), key="-SPEED-")
            ],
            [
                sg.Button("Summon Piece", key="-SUMMON-"),
                sg.Button("Reset Board", key="-RESET-"),
                sg.Button("Allow Illegal Moves: Off", key="-ILLEGAL-MOVES-")
            ],
            [
                sg.Text("FEN:"),
                sg.InputText(board.fen(), key="-FEN-", size=(50, 1)),
                sg.Button("Set FEN", key="-SET-FEN-"),
                sg.Button("Copy FEN", key="-COPY-FEN-")
            ],
            [sg.Button("Quit", key="-QUIT-")],
            [sg.Text("Move List:")],
            [sg.Listbox(values=[], size=(60, 10), key='-MOVE-LIST-', enable_events=True)],
        ]

        control_window = sg.Window("Analysis Controls", control_layout, finalize=True)

        # Function to update the board and controls
        def update_board_and_controls(highlight_squares=None):
            update_board_window(
                board_window, board, player_side=player_side, highlighted_squares=highlight_squares
            )
            control_window["-FEN-"].update(board.fen())

            # Build move list
            moves = []
            node = game
            while node != current_node and node.variations:
                next_node = node.variations[0]
                try:
                    move_san = node.board().san(next_node.move)
                except Exception:
                    move_san = next_node.move.uci()
                moves.append(move_san)
                node = next_node
            control_window['-MOVE-LIST-'].update(moves)
            if moves:
                control_window['-MOVE-LIST-'].set_value([moves[-1]])

        update_board_and_controls()

        # Function to make a move
        def make_move(move):
            nonlocal current_node, current_move_index, game_over
            if move is None:
                sg.popup_error("Move is not properly assigned. Please try again.")
                return False
            try:
                # Check if the move would capture a king
                target_piece = board.piece_at(move.to_square)
                if target_piece and target_piece.piece_type == chess.KING:
                    sg.popup("Cannot capture the king. This move results in checkmate.")
                    # Declare checkmate
                    result = "1-0" if board.turn == chess.WHITE else "0-1"
                    game.headers["Result"] = result
                    game_over = True
                    update_board_and_controls()
                    return False

                # Apply the move
                board.push(move)
                move_history.append(move)
                current_move_index += 1
                new_node = current_node.add_variation(move)
                current_node = new_node
                update_board_and_controls(highlight_squares={move.from_square, move.to_square})

                # Check if both kings are present after the move
                if not has_both_kings(board):
                    sg.popup("A king is missing from the board. This results in checkmate.")
                    result = "1-0" if board.turn == chess.BLACK else "0-1"
                    game.headers["Result"] = result
                    game_over = True

                return True
            except Exception as e:
                sg.popup_error(f"Error making move: {e}")
                return False

        # Function to summon a piece
        def summon_piece():
            nonlocal current_node, move_history, current_move_index
            piece_symbols = ['P', 'N', 'B', 'R', 'Q', 'K']
            colors = {'White': chess.WHITE, 'Black': chess.BLACK}

            # Select color
            color_event, _ = sg.Window("Select Color", [
                [sg.Text("Select piece color:")],
                [sg.Button("White"), sg.Button("Black")],
                [sg.Button("Cancel")]
            ], modal=True).read(close=True)

            if color_event in colors:
                piece_color = colors[color_event]
            else:
                sg.popup("Summoning piece cancelled.")
                return

            # Select piece type
            piece_event, _ = sg.Window("Summon Piece", [
                [sg.Text("Select a piece to summon:")],
                [sg.Button(symbol) for symbol in piece_symbols],
                [sg.Button("Cancel")]
            ], modal=True).read(close=True)

            if piece_event in piece_symbols:
                piece_type_dict = {
                    'P': chess.PAWN, 'N': chess.KNIGHT, 'B': chess.BISHOP,
                    'R': chess.ROOK, 'Q': chess.QUEEN, 'K': chess.KING
                }
                summoning_piece = chess.Piece(piece_type_dict[piece_event], piece_color)
                sg.popup("Now click on the board to place the piece.")
            else:
                sg.popup("Summoning piece cancelled.")
                return

            while True:
                board_event, _ = board_window.read(timeout=100)

                if board_event == sg.WIN_CLOSED:
                    break

                if isinstance(board_event, tuple) and len(board_event) == 2:
                    gui_rank, gui_file = board_event

                    # Adjust rank and file according to player_side
                    if player_side == 'white':
                        rank = gui_rank
                        file = gui_file
                    else:
                        rank = 7 - gui_rank
                        file = 7 - gui_file

                    square = chess.square(file, rank)

                    # Place or replace the piece at the selected square
                    board.set_piece_at(square, summoning_piece)
                    # Enforce single king per side
                    enforce_single_king_per_side(board)
                    # Record the action as a null move
                    current_node = current_node.add_variation(chess.Move.null())
                    move_history.append(chess.Move.null())
                    current_move_index += 1
                    update_board_and_controls()
                    sg.popup("Piece placed successfully!")
                    break

        # Main event loop
        while True:
            if game_over:
                result = game.headers.get("Result", "1/2-1/2")
                winner = "White" if result == "1-0" else "Black" if result == "0-1" else "Draw"
                sg.popup(f'Game over. Result: {result}. Winner: {winner}')
                break

            window, event, values = sg.read_all_windows(timeout=100)
            if event in (sg.WIN_CLOSED, "-QUIT-"):
                break

            # Control window events
            if window == control_window:
                if event == "-ENGINE-":
                    selected_engine = values['-ENGINE-']
                elif event == "-ANALYZE-":
                    if not has_both_kings(board):
                        sg.popup("Cannot analyze an invalid board position. Ensure both kings are present.")
                        continue
                    engine = engines[selected_engine]
                    result = engine.analyse(board, chess.engine.Limit(time=0.1))
                    best_move = result.get('pv', [None])[0]
                    highlight = {best_move.from_square, best_move.to_square} if best_move else None
                    update_board_and_controls(highlight_squares=highlight)
                elif event == "-HINT-":
                    if not has_both_kings(board):
                        sg.popup("Cannot provide a hint on an invalid board position. Ensure both kings are present.")
                        continue
                    engine = engines[selected_engine]
                    result = engine.analyse(board, chess.engine.Limit(time=0.1))
                    best_move = result.get('pv', [None])[0]
                    highlight = {best_move.from_square, best_move.to_square} if best_move else None
                    update_board_and_controls(highlight_squares=highlight)
                elif event in ("-NEXT-", ">"):
                    if current_node.variations:
                        current_node = current_node.variations[0]
                        board = current_node.board()
                        update_board_and_controls()
                elif event in ("-PREV-", "<"):
                    if current_node.parent:
                        current_node = current_node.parent
                        board = current_node.board()
                        update_board_and_controls()
                elif event == "-START-":
                    current_node = game
                    board = current_node.board()
                    update_board_and_controls()
                elif event == "-END-":
                    while current_node.variations:
                        current_node = current_node.variations[0]
                    board = current_node.board()
                    update_board_and_controls()
                elif event == "-AUTOPLAY-":
                    autoplay = not autoplay
                    control_window["-AUTOPLAY-"].update(f"Autoplay: {'On' if autoplay else 'Off'}")
                elif event == "-SPEED-":
                    autoplay_speed = values["-SPEED-"]
                elif event == "-SUMMON-":
                    summon_piece()
                elif event == "-RESET-":
                    board.reset()
                    enforce_single_king_per_side(board)
                    game = chess.pgn.Game()
                    current_node = game
                    move_history.clear()
                    current_move_index = 0
                    selected_square = None
                    update_board_and_controls()
                elif event == "-ROTATE-":
                    player_side = 'black' if player_side == 'white' else 'white'
                    board_window.close()
                    board_window = create_board_window(board, player_side=player_side)
                    update_board_and_controls()
                elif event == "-COPY-FEN-":
                    sg.clipboard_set(board.fen())
                    sg.popup("FEN copied to clipboard!")
                elif event == "-SET-FEN-":
                    fen_input = values["-FEN-"]
                    try:
                        board.set_fen(fen_input)
                        enforce_single_king_per_side(board)
                        game = chess.pgn.Game()
                        current_node = game
                        move_history.clear()
                        current_move_index = 0
                        selected_square = None
                        update_board_and_controls()
                    except ValueError as e:
                        sg.popup_error(f"Invalid FEN string: {e}")
                elif event == '-MOVE-LIST-':
                    selected_moves = values['-MOVE-LIST-']
                    if selected_moves:
                        current_node = game
                        board = current_node.board()
                        for move_san in selected_moves:
                            found = False
                            for variation in current_node.variations:
                                try:
                                    san = current_node.board().san(variation.move)
                                except Exception:
                                    san = variation.move.uci()
                                if san == move_san:
                                    current_node = variation
                                    board = current_node.board()
                                    found = True
                                    break
                            if not found:
                                break
                        update_board_and_controls()
                elif event == "-ILLEGAL-MOVES-":
                    allow_illegal_moves = not allow_illegal_moves
                    control_window["-ILLEGAL-MOVES-"].update(
                        f"Allow Illegal Moves: {'On' if allow_illegal_moves else 'Off'}"
                    )

            # Board window events
            if window == board_window:
                if event == sg.WIN_CLOSED:
                    break

                if isinstance(event, tuple):
                    gui_rank, gui_file = event

                    # Adjust rank and file according to player_side
                    if player_side == 'white':
                        rank = gui_rank
                        file = gui_file
                    else:
                        rank = 7 - gui_rank
                        file = 7 - gui_file

                    square = chess.square(file, rank)

                    if selected_square is None:
                        piece = board.piece_at(square)
                        if piece and (allow_illegal_moves or piece.color == board.turn):
                            # Select the piece
                            selected_square = square
                            if allow_illegal_moves:
                                # Highlight all squares
                                highlight_squares = set(chess.SQUARES)
                            else:
                                legal_moves = [
                                    move for move in board.legal_moves if move.from_square == square
                                ]
                                highlight_squares = {move.to_square for move in legal_moves}
                            update_board_and_controls(highlight_squares=highlight_squares)
                        else:
                            # Deselect if clicking on an empty square or opponent's piece
                            selected_square = None
                            update_board_and_controls()
                    else:
                        # Attempt to move the selected piece
                        if allow_illegal_moves:
                            # Move the piece directly
                            piece = board.piece_at(selected_square)
                            board.remove_piece_at(selected_square)
                            board.set_piece_at(square, piece)
                            # Enforce single king per side
                            enforce_single_king_per_side(board)
                            # Record the action as a null move
                            current_node = current_node.add_variation(chess.Move.null())
                            move_history.append(chess.Move.null())
                            current_move_index += 1
                            selected_square = None
                            update_board_and_controls()
                        else:
                            # Generate all legal moves from selected_square to square
                            possible_moves = [
                                m for m in board.legal_moves
                                if m.from_square == selected_square and m.to_square == square
                            ]
                            if not possible_moves:
                                # No legal moves to that square
                                selected_square = None
                                update_board_and_controls()
                            else:
                                if len(possible_moves) == 1 and not is_pawn_promotion(
                                    possible_moves[0], board
                                ):
                                    # Only one legal move, and it's not a promotion
                                    move = possible_moves[0]
                                    if make_move(move):
                                        selected_square = None
                                        update_board_and_controls()
                                else:
                                    # Either multiple promotion options or a promotion move
                                    promotion_piece = pawn_promotion(
                                        'w' if board.turn == chess.WHITE else 'b'
                                    )
                                    if promotion_piece is None:
                                        # Promotion cancelled
                                        selected_square = None
                                        update_board_and_controls()
                                        continue
                                    # Find the move with the selected promotion piece
                                    move = None
                                    for m in possible_moves:
                                        if m.promotion == promotion_piece:
                                            move = m
                                            break
                                    if move is None:
                                        sg.popup_error("Invalid promotion piece selected.")
                                        selected_square = None
                                        update_board_and_controls()
                                    else:
                                        if make_move(move):
                                            selected_square = None
                                            update_board_and_controls()

            # Autoplay logic
            if autoplay and (time.time() - last_autoplay_time) >= (1.0 / autoplay_speed):
                if not board.is_game_over() and not game_over:
                    if not has_both_kings(board):
                        sg.popup("A king is missing from the board. Autoplay stopped.")
                        autoplay = False
                        control_window["-AUTOPLAY-"].update("Autoplay: Off")
                        continue
                    engine = engines[selected_engine]
                    result = engine.play(board, chess.engine.Limit(depth=20))
                    move = result.move
                    if move is not None:
                        if is_pawn_promotion(move, board) and move.promotion is None:
                            # Set default promotion to Queen
                            move.promotion = chess.QUEEN
                        make_move(move)
                    else:
                        autoplay = False
                        control_window["-AUTOPLAY-"].update("Autoplay: Off")
                        sg.popup("Autoplay stopped: No valid moves available.")
                else:
                    autoplay = False
                    control_window["-AUTOPLAY-"].update("Autoplay: Off")
                    sg.popup("Autoplay stopped: Game over.")
                last_autoplay_time = time.time()

        # Close windows and save game
        board_window.close()
        control_window.close()
        save_game(game, analysis_path, allow_save=True)

    except Exception as e:
        sg.popup_error(f"Error during position analysis: {e}")

def main():
    try:
        sg.theme('DefaultNoMoreNagging')
        engines = get_engines()
        if not engines:
            sg.popup_error("No engines were loaded. Exiting the program.")
            return

        layout = [
            [sg.Text("Chess Game", font=("Helvetica", 24), justification='center')],
            [sg.Button("Play against an engine", key="HumanVSEngine", size=(30, 2))],
            [sg.Button("Play between two engines", key="EngineVSEngine", size=(30, 2))],
            [sg.Button("Analyze a position", key="Analyze", size=(30, 2))],
            [sg.Button("Quit", key="Quit", size=(30, 2))]
        ]

        window = sg.Window("Chess Game", layout, finalize=True, element_justification='c')

        while True:
            event, values = window.read()

            if event in (sg.WIN_CLOSED, "Quit"):
                break

            elif event == "HumanVSEngine":
                engine_name, difficulty = select_engine(engines)
                if engine_name:
                    human_side = select_side()
                    if human_side:
                        play_game(
                            human_side=human_side,
                            engine=engines[engine_name],
                            engines=engines,
                            main_window=window,
                            save_path=HUMAN_VS_ENGINE_PATH,
                            game_number=1,
                            difficulty=difficulty
                        )

            elif event == "EngineVSEngine":
                engine1_name, engine2_name, difficulty1, difficulty2 = select_two_engines(engines)
                if engine1_name and engine2_name:
                    engine1 = CustomEngine(engines[engine1_name], difficulty1)
                    engine2 = CustomEngine(engines[engine2_name], difficulty2)
                    engine_vs_engine_game(
                        engine1=engine1,
                        engine2=engine2,
                        main_window=window,
                        save_path=ENGINE_VS_ENGINE_PATH,
                        game_number=1,
                        engine1_name=engine1_name,
                        engine2_name=engine2_name
                    )

            elif event == "Analyze":
                mode = select_analysis_mode()
                if mode == "Cancel":
                    continue

                if mode == "LoadFEN":
                    fen_or_pgn_input = sg.popup_get_text('Enter FEN string:')
                    if fen_or_pgn_input:
                        analyze_position(
                            fen_or_pgn_input=fen_or_pgn_input,
                            main_window=window,
                            engines=engines,
                            analysis_path=ANALYSIS_PATH,
                            game_number=1
                        )
                elif mode == "LoadPGN":
                    fen_or_pgn_input = sg.popup_get_file(
                        'Select PGN file',
                        file_types=(("PGN Files", "*.pgn"),),
                        initial_folder=PGN_FOLDER_PATH
                    )
                    if fen_or_pgn_input and os.path.exists(fen_or_pgn_input):
                        analyze_position(
                            fen_or_pgn_input=fen_or_pgn_input,
                            main_window=window,
                            engines=engines,
                            analysis_path=ANALYSIS_PATH,
                            game_number=1
                        )
                elif mode == "Standard":
                    fen_or_pgn_input = chess.STARTING_FEN
                    analyze_position(
                        fen_or_pgn_input=fen_or_pgn_input,
                        main_window=window,
                        engines=engines,
                        analysis_path=ANALYSIS_PATH,
                        game_number=1
                    )
                elif mode == "Random":
                    board = generate_random_position()
                    analyze_position(
                        fen_or_pgn_input=board.fen(),
                        main_window=window,
                        engines=engines,
                        analysis_path=ANALYSIS_PATH,
                        game_number=1
                    )
                elif mode == "Clear":
                    fen_or_pgn_input = '8/8/8/8/8/8/8/8 w - - 0 1'  # Empty board
                    analyze_position(
                        fen_or_pgn_input=fen_or_pgn_input,
                        main_window=window,
                        engines=engines,
                        analysis_path=ANALYSIS_PATH,
                        game_number=1
                    )

        window.close()
        for engine in engines.values():
            engine.quit()

    except Exception as e:
        sg.popup_error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
