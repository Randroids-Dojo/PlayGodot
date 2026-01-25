extends CharacterBody2D
## Simple 2D platformer player with movement and jumping.
##
## Exposes methods for testing player state and movement.

signal jumped
signal landed
signal collected(item_name: String)
signal died

const SPEED = 200.0
const JUMP_VELOCITY = -350.0
const GRAVITY = 980.0

var coins_collected: int = 0
var is_alive: bool = true
var _was_on_floor: bool = false


func _physics_process(delta: float) -> void:
	if not is_alive:
		return

	# Add gravity
	if not is_on_floor():
		velocity.y += GRAVITY * delta

	# Detect landing
	if is_on_floor() and not _was_on_floor:
		landed.emit()
	_was_on_floor = is_on_floor()

	# Handle jump
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY
		jumped.emit()

	# Get horizontal movement direction
	var direction := Input.get_axis("move_left", "move_right")
	if direction:
		velocity.x = direction * SPEED
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED * 0.2)

	move_and_slide()


# --- Test API Methods ---

func get_position_x() -> float:
	"""Get current X position."""
	return position.x


func get_position_y() -> float:
	"""Get current Y position."""
	return position.y


func get_velocity_x() -> float:
	"""Get current X velocity."""
	return velocity.x


func get_velocity_y() -> float:
	"""Get current Y velocity."""
	return velocity.y


func is_grounded() -> bool:
	"""Check if player is on the floor."""
	return is_on_floor()


func is_jumping() -> bool:
	"""Check if player is moving upward (jumping)."""
	return velocity.y < 0 and not is_on_floor()


func is_falling() -> bool:
	"""Check if player is moving downward."""
	return velocity.y > 0 and not is_on_floor()


func get_coins() -> int:
	"""Get number of coins collected."""
	return coins_collected


func get_state() -> String:
	"""Get current player state as string."""
	if not is_alive:
		return "dead"
	if is_on_floor():
		if abs(velocity.x) > 10:
			return "running"
		return "idle"
	if velocity.y < 0:
		return "jumping"
	return "falling"


func collect_coin() -> void:
	"""Called when player collects a coin."""
	coins_collected += 1
	collected.emit("coin")


func die() -> void:
	"""Kill the player."""
	is_alive = false
	velocity = Vector2.ZERO
	died.emit()


func respawn(spawn_position: Vector2) -> void:
	"""Respawn player at position."""
	position = spawn_position
	velocity = Vector2.ZERO
	is_alive = true
	coins_collected = 0


func set_position_for_test(x: float, y: float) -> void:
	"""Set position directly (for testing)."""
	position = Vector2(x, y)
	velocity = Vector2.ZERO
