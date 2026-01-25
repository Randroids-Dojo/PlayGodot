extends Area2D
## Collectible coin that the player can pick up.

signal collected


func _ready() -> void:
	add_to_group("coins")
	add_to_group("collectibles")
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if body.has_method("collect_coin"):
		body.collect_coin()
		collected.emit()
		queue_free()


func get_value() -> int:
	"""Get coin value."""
	return 100
