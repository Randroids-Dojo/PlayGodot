"""Godot Variant binary serialization for Python.

Implements encoding/decoding of Godot's native binary Variant format
for communication with the RemoteDebugger automation protocol.

Based on actual Godot source code:
- core/variant/variant.h (type enum)
- core/io/marshalls.cpp (encode_variant, decode_variant)
- core/io/marshalls.h (encode_uint32, etc.)

Wire format for debugger protocol (from remote_debugger_peer.cpp):
- [4 bytes: size of variant data (little-endian uint32)]
- [N bytes: encoded variant]

Variant encoding (from marshalls.cpp):
- [4 bytes: header] - byte 0 is Variant::Type, bit 16 is 64-bit flag
- [N bytes: type-specific payload]
"""

from __future__ import annotations

import struct
from enum import IntEnum
from typing import Any


class VariantType(IntEnum):
    """Godot Variant type IDs from core/variant/variant.h."""
    NIL = 0
    BOOL = 1
    INT = 2
    FLOAT = 3
    STRING = 4
    VECTOR2 = 5
    VECTOR2I = 6
    RECT2 = 7
    RECT2I = 8
    VECTOR3 = 9
    VECTOR3I = 10
    TRANSFORM2D = 11
    VECTOR4 = 12
    VECTOR4I = 13
    PLANE = 14
    QUATERNION = 15
    AABB = 16
    BASIS = 17
    TRANSFORM3D = 18
    PROJECTION = 19
    COLOR = 20
    STRING_NAME = 21
    NODE_PATH = 22
    RID = 23
    OBJECT = 24
    CALLABLE = 25
    SIGNAL = 26
    DICTIONARY = 27
    ARRAY = 28
    PACKED_BYTE_ARRAY = 29
    PACKED_INT32_ARRAY = 30
    PACKED_INT64_ARRAY = 31
    PACKED_FLOAT32_ARRAY = 32
    PACKED_FLOAT64_ARRAY = 33
    PACKED_STRING_ARRAY = 34
    PACKED_VECTOR2_ARRAY = 35
    PACKED_VECTOR3_ARRAY = 36
    PACKED_COLOR_ARRAY = 37
    PACKED_VECTOR4_ARRAY = 38


# Header flags from marshalls.cpp
HEADER_DATA_FLAG_64 = 1 << 16


class VariantEncoder:
    """Encodes Python values to Godot Variant binary format."""

    def encode(self, value: Any) -> bytes:
        """Encode a Python value to Godot Variant format.

        Args:
            value: Python value (None, bool, int, float, str, list, dict, bytes)

        Returns:
            Encoded bytes (header + payload, no size prefix)
        """
        if value is None:
            return self._encode_nil()
        elif isinstance(value, bool):
            # Must check bool before int since bool is subclass of int
            return self._encode_bool(value)
        elif isinstance(value, int):
            return self._encode_int(value)
        elif isinstance(value, float):
            return self._encode_float(value)
        elif isinstance(value, str):
            return self._encode_string(value)
        elif isinstance(value, (list, tuple)):
            return self._encode_array(value)
        elif isinstance(value, dict):
            return self._encode_dictionary(value)
        elif isinstance(value, bytes):
            return self._encode_packed_byte_array(value)
        else:
            raise TypeError(f"Cannot encode type {type(value).__name__}")

    def _encode_nil(self) -> bytes:
        """NIL: just header, no payload."""
        return struct.pack("<I", VariantType.NIL)

    def _encode_bool(self, value: bool) -> bytes:
        """BOOL: header + uint32 (0 or 1)."""
        return struct.pack("<II", VariantType.BOOL, 1 if value else 0)

    def _encode_int(self, value: int) -> bytes:
        """INT: header + int32 or int64 depending on range."""
        # From marshalls.cpp: use 64-bit if > INT_MAX or < INT_MIN
        if -2147483648 <= value <= 2147483647:
            return struct.pack("<Ii", VariantType.INT, value)
        else:
            header = VariantType.INT | HEADER_DATA_FLAG_64
            return struct.pack("<Iq", header, value)

    def _encode_float(self, value: float) -> bytes:
        """FLOAT: header + float32 or float64.

        From marshalls.cpp: use 64-bit if double(float(d)) != d
        We always use 64-bit to preserve precision.
        """
        header = VariantType.FLOAT | HEADER_DATA_FLAG_64
        return struct.pack("<Id", header, value)

    def _encode_string(self, value: str) -> bytes:
        """STRING: header + length + UTF-8 bytes + padding.

        From _encode_string in marshalls.cpp:
        - encode_uint32(utf8.length(), buf)
        - memcpy(buf, utf8.get_data(), utf8.length())
        - pad to 4-byte boundary
        """
        utf8 = value.encode("utf-8")
        length = len(utf8)
        # Pad to 4-byte boundary
        pad_len = (4 - length % 4) % 4
        padded = utf8 + b"\x00" * pad_len

        return struct.pack("<II", VariantType.STRING, length) + padded

    def _encode_array(self, value: list | tuple) -> bytes:
        """ARRAY: header + count + encoded elements.

        From marshalls.cpp (untyped array):
        - encode_uint32(array.size(), buf)
        - for each element: encode_variant(elem, buf, ...)
        """
        parts = [struct.pack("<II", VariantType.ARRAY, len(value))]
        for item in value:
            parts.append(self.encode(item))
        return b"".join(parts)

    def _encode_dictionary(self, value: dict) -> bytes:
        """DICTIONARY: header + count + key/value pairs.

        From marshalls.cpp (untyped dict):
        - encode_uint32(dict.size(), buf)
        - for each key, value: encode_variant(key), encode_variant(value)
        """
        parts = [struct.pack("<II", VariantType.DICTIONARY, len(value))]
        for k, v in value.items():
            parts.append(self.encode(k))
            parts.append(self.encode(v))
        return b"".join(parts)

    def _encode_packed_byte_array(self, value: bytes) -> bytes:
        """PACKED_BYTE_ARRAY: header + length + data + padding."""
        length = len(value)
        pad_len = (4 - length % 4) % 4
        padded = value + b"\x00" * pad_len
        return struct.pack("<II", VariantType.PACKED_BYTE_ARRAY, length) + padded


class VariantDecoder:
    """Decodes Godot Variant binary format to Python values."""

    def decode(self, data: bytes, offset: int = 0) -> tuple[Any, int]:
        """Decode a Godot Variant from binary format.

        Args:
            data: Binary data
            offset: Starting offset in data

        Returns:
            Tuple of (decoded value, total bytes consumed including header)
        """
        if len(data) - offset < 4:
            raise ValueError("Buffer too short for variant header")

        header = struct.unpack_from("<I", data, offset)[0]
        variant_type = header & 0xFF
        is_64bit = bool(header & HEADER_DATA_FLAG_64)

        payload_offset = offset + 4
        consumed = 4  # header

        if variant_type == VariantType.NIL:
            return None, consumed

        elif variant_type == VariantType.BOOL:
            val = struct.unpack_from("<I", data, payload_offset)[0]
            return bool(val), consumed + 4

        elif variant_type == VariantType.INT:
            if is_64bit:
                val = struct.unpack_from("<q", data, payload_offset)[0]
                return val, consumed + 8
            else:
                val = struct.unpack_from("<i", data, payload_offset)[0]
                return val, consumed + 4

        elif variant_type == VariantType.FLOAT:
            if is_64bit:
                val = struct.unpack_from("<d", data, payload_offset)[0]
                return val, consumed + 8
            else:
                val = struct.unpack_from("<f", data, payload_offset)[0]
                return val, consumed + 4

        elif variant_type == VariantType.STRING:
            val, bytes_read = self._decode_string(data, payload_offset)
            return val, consumed + bytes_read

        elif variant_type == VariantType.STRING_NAME:
            # STRING_NAME uses same encoding as STRING
            val, bytes_read = self._decode_string(data, payload_offset)
            return val, consumed + bytes_read

        elif variant_type == VariantType.NODE_PATH:
            # NODE_PATH: complex format, but we only need to decode simple paths
            val, bytes_read = self._decode_node_path(data, payload_offset)
            return val, consumed + bytes_read

        elif variant_type == VariantType.VECTOR2:
            if is_64bit:
                x, y = struct.unpack_from("<dd", data, payload_offset)
                return {"x": x, "y": y, "_type": "Vector2"}, consumed + 16
            else:
                x, y = struct.unpack_from("<ff", data, payload_offset)
                return {"x": x, "y": y, "_type": "Vector2"}, consumed + 8

        elif variant_type == VariantType.VECTOR2I:
            x, y = struct.unpack_from("<ii", data, payload_offset)
            return {"x": x, "y": y, "_type": "Vector2i"}, consumed + 8

        elif variant_type == VariantType.VECTOR3:
            if is_64bit:
                x, y, z = struct.unpack_from("<ddd", data, payload_offset)
                return {"x": x, "y": y, "z": z, "_type": "Vector3"}, consumed + 24
            else:
                x, y, z = struct.unpack_from("<fff", data, payload_offset)
                return {"x": x, "y": y, "z": z, "_type": "Vector3"}, consumed + 12

        elif variant_type == VariantType.VECTOR3I:
            x, y, z = struct.unpack_from("<iii", data, payload_offset)
            return {"x": x, "y": y, "z": z, "_type": "Vector3i"}, consumed + 12

        elif variant_type == VariantType.COLOR:
            r, g, b, a = struct.unpack_from("<ffff", data, payload_offset)
            return {"r": r, "g": g, "b": b, "a": a, "_type": "Color"}, consumed + 16

        elif variant_type == VariantType.ARRAY:
            # For ARRAY, the is_64bit flag indicates a typed array (not 64-bit data)
            val, bytes_read = self._decode_array(data, payload_offset, is_typed_array=is_64bit)
            return val, consumed + bytes_read

        elif variant_type == VariantType.DICTIONARY:
            val, bytes_read = self._decode_dictionary(data, payload_offset)
            return val, consumed + bytes_read

        elif variant_type == VariantType.PACKED_BYTE_ARRAY:
            length = struct.unpack_from("<I", data, payload_offset)[0]
            payload_offset += 4
            val = data[payload_offset:payload_offset + length]
            # Account for padding
            padded_len = length + (4 - length % 4) % 4
            return val, consumed + 4 + padded_len

        elif variant_type == VariantType.PACKED_INT32_ARRAY:
            length = struct.unpack_from("<I", data, payload_offset)[0]
            payload_offset += 4
            result = []
            for i in range(length):
                result.append(struct.unpack_from("<i", data, payload_offset + i * 4)[0])
            return result, consumed + 4 + length * 4

        elif variant_type == VariantType.PACKED_INT64_ARRAY:
            length = struct.unpack_from("<I", data, payload_offset)[0]
            payload_offset += 4
            result = []
            for i in range(length):
                result.append(struct.unpack_from("<q", data, payload_offset + i * 8)[0])
            return result, consumed + 4 + length * 8

        elif variant_type == VariantType.PACKED_FLOAT32_ARRAY:
            length = struct.unpack_from("<I", data, payload_offset)[0]
            payload_offset += 4
            result = []
            for i in range(length):
                result.append(struct.unpack_from("<f", data, payload_offset + i * 4)[0])
            return result, consumed + 4 + length * 4

        elif variant_type == VariantType.PACKED_FLOAT64_ARRAY:
            length = struct.unpack_from("<I", data, payload_offset)[0]
            payload_offset += 4
            result = []
            for i in range(length):
                result.append(struct.unpack_from("<d", data, payload_offset + i * 8)[0])
            return result, consumed + 4 + length * 8

        elif variant_type == VariantType.PACKED_STRING_ARRAY:
            length = struct.unpack_from("<I", data, payload_offset)[0]
            current = payload_offset + 4
            total_consumed = 4
            result = []
            for _ in range(length):
                s, bytes_read = self._decode_string(data, current)
                result.append(s)
                current += bytes_read
                total_consumed += bytes_read
            return result, consumed + total_consumed

        elif variant_type == VariantType.RID:
            # RID: 64-bit integer
            val = struct.unpack_from("<Q", data, payload_offset)[0]
            return {"_type": "RID", "id": val}, consumed + 8

        elif variant_type == VariantType.OBJECT:
            # Object encoding is complex - for now return None
            # Real implementation would need class info, property list, etc.
            return None, consumed

        else:
            raise ValueError(f"Unsupported variant type: {variant_type}")

    def _decode_string(self, data: bytes, offset: int) -> tuple[str, int]:
        """Decode string: length + UTF-8 bytes + padding."""
        length = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        value = data[offset:offset + length].decode("utf-8")
        # Account for padding
        pad_len = (4 - length % 4) % 4
        return value, 4 + length + pad_len

    def _decode_node_path(self, data: bytes, offset: int) -> tuple[str, int]:
        """Decode NODE_PATH (new format from Godot 4).

        From marshalls.cpp:
        - First uint32: namecount | 0x80000000 (new format flag)
        - Second uint32: subnamecount
        - Third uint32: flags (bit 0 = absolute)
        - Then: strings for names and subnames
        """
        first = struct.unpack_from("<I", data, offset)[0]

        if not (first & 0x80000000):
            # Old format not supported
            raise ValueError("Old NODE_PATH format not supported")

        namecount = first & 0x7FFFFFFF
        subnamecount = struct.unpack_from("<I", data, offset + 4)[0]
        flags = struct.unpack_from("<I", data, offset + 8)[0]

        current = offset + 12
        consumed = 12

        names = []
        subnames = []
        total = namecount + subnamecount

        for i in range(total):
            s, bytes_read = self._decode_string(data, current)
            current += bytes_read
            consumed += bytes_read
            if i < namecount:
                names.append(s)
            else:
                subnames.append(s)

        # Reconstruct path string
        path = "/".join(names)
        if flags & 1:  # absolute
            path = "/" + path
        if subnames:
            path += ":" + ":".join(subnames)

        return path, consumed

    def _decode_array(self, data: bytes, offset: int, is_typed_array: bool = False) -> tuple[list, int]:
        """Decode array: count + elements.

        For typed arrays (Array[T]), the header has HEADER_DATA_FLAG_64 set,
        and the payload format is: [type_info: 4 bytes] [count: 4 bytes] [elements]
        For untyped arrays: [count: 4 bytes] [elements]
        """
        current = offset
        consumed = 0

        if is_typed_array:
            # Typed array: [type_info][count][elements]
            type_info = struct.unpack_from("<I", data, current)[0]
            current += 4
            consumed += 4

            count = struct.unpack_from("<I", data, current)[0]
            current += 4
            consumed += 4
        else:
            # Untyped array: [count][elements]
            # Count may have flags in high bits
            raw_count = struct.unpack_from("<I", data, offset)[0]
            count = raw_count & 0x7FFFFFFF  # Clear potential shared flag
            current = offset + 4
            consumed = 4

        result = []
        for _ in range(count):
            item, bytes_read = self.decode(data, current)
            result.append(item)
            current += bytes_read
            consumed += bytes_read

        return result, consumed

    def _decode_dictionary(self, data: bytes, offset: int) -> tuple[dict, int]:
        """Decode dictionary: count + key/value pairs."""
        count = struct.unpack_from("<I", data, offset)[0]
        count &= 0x7FFFFFFF  # Clear potential shared flag
        current = offset + 4
        consumed = 4

        result = {}
        for _ in range(count):
            key, key_bytes = self.decode(data, current)
            current += key_bytes
            consumed += key_bytes

            val, val_bytes = self.decode(data, current)
            current += val_bytes
            consumed += val_bytes

            # Convert key to appropriate hashable type
            if isinstance(key, dict):
                key = str(key)
            result[key] = val

        return result, consumed


# Module-level instances for convenience
_encoder = VariantEncoder()
_decoder = VariantDecoder()


def encode_variant(value: Any) -> bytes:
    """Encode a Python value to Godot Variant binary format."""
    return _encoder.encode(value)


def decode_variant(data: bytes, offset: int = 0) -> tuple[Any, int]:
    """Decode a Godot Variant from binary format."""
    return _decoder.decode(data, offset)


def encode_message(name: str, thread_id: int, data: list) -> bytes:
    """Encode a debugger protocol message with size prefix.

    The debugger protocol uses: [4-byte size][encoded Array]
    where the Array is [message_name, thread_id, data_array]

    Args:
        name: Message name (e.g., "automation:get_tree")
        thread_id: Thread ID (usually 0 for automation)
        data: Message data as a list

    Returns:
        Encoded message with 4-byte size prefix
    """
    message = [name, thread_id, data]
    encoded = encode_variant(message)
    # Prefix with 4-byte length (from remote_debugger_peer.cpp _write_out)
    return struct.pack("<I", len(encoded)) + encoded


def decode_message(data: bytes) -> tuple[str, int, list]:
    """Decode a debugger protocol message (without size prefix).

    Args:
        data: Raw variant data (size prefix already stripped)

    Returns:
        Tuple of (message_name, thread_id, data_list)
    """
    message, _ = decode_variant(data)
    if not isinstance(message, list) or len(message) != 3:
        raise ValueError(f"Invalid message format: expected [name, thread_id, data], got {type(message)}")
    return message[0], message[1], message[2]