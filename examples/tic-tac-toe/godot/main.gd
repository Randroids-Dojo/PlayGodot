extends Control
## Tic Tac Toe game for PlayGodot testing.

signal game_over(winner: String)
signal turn_changed(player: String)

const EMPTY = ""
const X = "X"
const O = "O"

var board: Array[String] = []
var current_player: String = X
var game_active: bool = true
var winner: String = ""

@onready var cells: Array[Button] = []
@onready var status_label: Label = $StatusLabel
@onready var restart_button: Button = $RestartButton


func _ready() -> void:
	# Get all cell buttons
	for i in range(9):
		var cell = get_node("Board/Cell%d" % i) as Button
		cells.append(cell)
		cell.pressed.connect(_on_cell_pressed.bind(i))

	restart_button.pressed.connect(_on_restart_pressed)
	_reset_game()


func _reset_game() -> void:
	board = []
	for i in range(9):
		board.append(EMPTY)
		cells[i].text = ""
		cells[i].disabled = false

	current_player = X
	game_active = true
	winner = ""
	_update_status()


func _on_cell_pressed(index: int) -> void:
	if not game_active:
		return

	if board[index] != EMPTY:
		return

	# Make the move
	board[index] = current_player
	cells[index].text = current_player

	# Check for winner
	winner = _check_winner()
	if winner != "":
		game_active = false
		_update_status()
		game_over.emit(winner)
		return

	# Check for draw
	if _is_board_full():
		game_active = false
		winner = "Draw"
		_update_status()
		game_over.emit("Draw")
		return

	# Switch player
	current_player = O if current_player == X else X
	_update_status()
	turn_changed.emit(current_player)


func _check_winner() -> String:
	# Winning combinations
	var lines = [
		[0, 1, 2],  # Top row
		[3, 4, 5],  # Middle row
		[6, 7, 8],  # Bottom row
		[0, 3, 6],  # Left column
		[1, 4, 7],  # Middle column
		[2, 5, 8],  # Right column
		[0, 4, 8],  # Diagonal
		[2, 4, 6],  # Anti-diagonal
	]

	for line in lines:
		var a = board[line[0]]
		var b = board[line[1]]
		var c = board[line[2]]
		if a != EMPTY and a == b and b == c:
			# Disable all cells on win
			for cell in cells:
				cell.disabled = true
			return a

	return ""


func _is_board_full() -> bool:
	for cell in board:
		if cell == EMPTY:
			return false
	return true


func _update_status() -> void:
	if winner == "Draw":
		status_label.text = "It's a draw!"
	elif winner != "":
		status_label.text = "%s wins!" % winner
	else:
		status_label.text = "%s's turn" % current_player


func _on_restart_pressed() -> void:
	_reset_game()


## API methods for testing

func get_board() -> Array[String]:
	return board.duplicate()


func get_current_player() -> String:
	return current_player


func get_winner() -> String:
	return winner


func is_game_active() -> bool:
	return game_active


func make_move(index: int) -> bool:
	"""Make a move programmatically. Returns true if successful."""
	if not game_active:
		return false
	if index < 0 or index > 8:
		return false
	if board[index] != EMPTY:
		return false

	_on_cell_pressed(index)
	return true


func get_cell_text(index: int) -> String:
	if index < 0 or index > 8:
		return ""
	return board[index]
