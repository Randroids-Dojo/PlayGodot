@tool
extends EditorPlugin
## PlayGodot Editor Plugin
##
## Manages the automation server lifecycle for the PlayGodot testing framework.

const AutomateServer = preload("res://addons/playgodot/server.gd")

var _server: Node = null


func _enter_tree() -> void:
	# Only start server in debug/play mode, not in editor
	if not Engine.is_editor_hint():
		_start_server()


func _exit_tree() -> void:
	_stop_server()


func _start_server() -> void:
	if _server != null:
		return

	_server = AutomateServer.new()
	_server.name = "PlayGodotServer"

	# Add to root so it persists across scene changes
	get_tree().root.add_child.call_deferred(_server)

	print("[PlayGodot] Automation server started")


func _stop_server() -> void:
	if _server != null:
		_server.queue_free()
		_server = null
		print("[PlayGodot] Automation server stopped")
