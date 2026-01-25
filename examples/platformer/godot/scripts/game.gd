extends Node2D
## Main game controller for the platformer.
##
## Manages game state, scoring, and level transitions.

signal game_paused
signal game_resumed
signal level_completed(level_name: String)
signal score_changed(new_score: int)

@onready var player: CharacterBody2D = $Player
@onready var hud: CanvasLayer = $HUD
@onready var score_label: Label = $HUD/ScoreLabel
@onready var status_label: Label = $HUD/StatusLabel
@onready var pause_menu: Control = $HUD/PauseMenu

var score: int = 0
var total_coins: int = 0
var level_name: String = "Level 1"
var _spawn_position: Vector2


func _ready() -> void:
	_spawn_position = player.position
	_count_coins()
	_update_hud()
	pause_menu.visible = false

	# Connect player signals
	player.collected.connect(_on_player_collected)
	player.died.connect(_on_player_died)


func _count_coins() -> void:
	"""Count total coins in level."""
	total_coins = get_tree().get_nodes_in_group("coins").size()


func _process(_delta: float) -> void:
	if Input.is_action_just_pressed("pause"):
		toggle_pause()
	if Input.is_action_just_pressed("restart"):
		restart_level()


func _update_hud() -> void:
	score_label.text = "Score: %d" % score
	if total_coins > 0:
		var collected = player.get_coins() if player else 0
		status_label.text = "Coins: %d / %d" % [collected, total_coins]
	else:
		status_label.text = level_name


# --- Game Control API ---

func toggle_pause() -> void:
	"""Toggle game pause state."""
	get_tree().paused = not get_tree().paused
	pause_menu.visible = get_tree().paused
	if get_tree().paused:
		game_paused.emit()
	else:
		game_resumed.emit()


func set_paused(paused: bool) -> void:
	"""Set pause state directly."""
	get_tree().paused = paused
	pause_menu.visible = paused


func is_paused() -> bool:
	"""Check if game is paused."""
	return get_tree().paused


func restart_level() -> void:
	"""Restart the current level."""
	get_tree().paused = false
	pause_menu.visible = false
	get_tree().reload_current_scene()


func get_score() -> int:
	"""Get current score."""
	return score


func add_score(points: int) -> void:
	"""Add points to score."""
	score += points
	score_changed.emit(score)
	_update_hud()


func get_player_coins() -> int:
	"""Get coins collected by player."""
	return player.get_coins() if player else 0


func get_total_coins() -> int:
	"""Get total coins in level."""
	return total_coins


func get_remaining_coins() -> int:
	"""Get remaining coins to collect."""
	return total_coins - get_player_coins()


func is_level_complete() -> bool:
	"""Check if all coins collected."""
	return get_remaining_coins() == 0


func get_level_name() -> String:
	"""Get current level name."""
	return level_name


func get_player_state() -> String:
	"""Get player state string."""
	return player.get_state() if player else "none"


func get_player_position() -> Dictionary:
	"""Get player position as dict."""
	if player:
		return {"x": player.position.x, "y": player.position.y}
	return {"x": 0, "y": 0}


func respawn_player() -> void:
	"""Respawn the player at start."""
	if player:
		player.respawn(_spawn_position)
	_update_hud()


func get_coin_count() -> int:
	"""Get number of coin nodes remaining in scene."""
	return get_tree().get_nodes_in_group("coins").size()


func get_nodes_in_group(group_name: String) -> Array:
	"""Get all node paths in a group."""
	var paths: Array = []
	for node in get_tree().get_nodes_in_group(group_name):
		paths.append(str(node.get_path()))
	return paths


# --- Signal Handlers ---

func _on_player_collected(item_name: String) -> void:
	if item_name == "coin":
		add_score(100)
		_update_hud()
		if is_level_complete():
			level_completed.emit(level_name)


func _on_player_died() -> void:
	status_label.text = "Game Over! Press R to restart"
