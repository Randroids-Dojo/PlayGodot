"""Comprehensive tests for Godot Variant binary serialization."""

import struct
import pytest
from playgodot.variant import (
    VariantType,
    VariantEncoder,
    VariantDecoder,
    HEADER_DATA_FLAG_64,
    encode_variant,
    decode_variant,
    encode_message,
    decode_message,
)


class TestVariantType:
    """Tests for VariantType enum values."""

    def test_variant_type_nil(self) -> None:
        assert VariantType.NIL == 0

    def test_variant_type_bool(self) -> None:
        assert VariantType.BOOL == 1

    def test_variant_type_int(self) -> None:
        assert VariantType.INT == 2

    def test_variant_type_float(self) -> None:
        assert VariantType.FLOAT == 3

    def test_variant_type_string(self) -> None:
        assert VariantType.STRING == 4

    def test_variant_type_array(self) -> None:
        assert VariantType.ARRAY == 28

    def test_variant_type_dictionary(self) -> None:
        assert VariantType.DICTIONARY == 27

    def test_variant_type_packed_byte_array(self) -> None:
        assert VariantType.PACKED_BYTE_ARRAY == 29

    def test_header_data_flag_64(self) -> None:
        assert HEADER_DATA_FLAG_64 == 0x10000


class TestVariantEncoderPrimitives:
    """Tests for VariantEncoder primitive types."""

    def setup_method(self) -> None:
        self.encoder = VariantEncoder()

    def test_encode_nil(self) -> None:
        result = self.encoder.encode(None)
        assert result == struct.pack("<I", VariantType.NIL)

    def test_encode_bool_true(self) -> None:
        result = self.encoder.encode(True)
        assert result == struct.pack("<II", VariantType.BOOL, 1)

    def test_encode_bool_false(self) -> None:
        result = self.encoder.encode(False)
        assert result == struct.pack("<II", VariantType.BOOL, 0)

    def test_encode_int_zero(self) -> None:
        result = self.encoder.encode(0)
        assert result == struct.pack("<Ii", VariantType.INT, 0)

    def test_encode_int_positive(self) -> None:
        result = self.encoder.encode(42)
        assert result == struct.pack("<Ii", VariantType.INT, 42)

    def test_encode_int_negative(self) -> None:
        result = self.encoder.encode(-100)
        assert result == struct.pack("<Ii", VariantType.INT, -100)

    def test_encode_int_max_32bit(self) -> None:
        result = self.encoder.encode(2147483647)
        assert result == struct.pack("<Ii", VariantType.INT, 2147483647)

    def test_encode_int_min_32bit(self) -> None:
        result = self.encoder.encode(-2147483648)
        assert result == struct.pack("<Ii", VariantType.INT, -2147483648)

    def test_encode_int_64bit_positive(self) -> None:
        val = 2147483648  # INT_MAX + 1
        result = self.encoder.encode(val)
        expected_header = VariantType.INT | HEADER_DATA_FLAG_64
        assert result == struct.pack("<Iq", expected_header, val)

    def test_encode_int_64bit_negative(self) -> None:
        val = -2147483649  # INT_MIN - 1
        result = self.encoder.encode(val)
        expected_header = VariantType.INT | HEADER_DATA_FLAG_64
        assert result == struct.pack("<Iq", expected_header, val)

    def test_encode_float_zero(self) -> None:
        result = self.encoder.encode(0.0)
        expected_header = VariantType.FLOAT | HEADER_DATA_FLAG_64
        assert result == struct.pack("<Id", expected_header, 0.0)

    def test_encode_float_positive(self) -> None:
        result = self.encoder.encode(3.14159)
        expected_header = VariantType.FLOAT | HEADER_DATA_FLAG_64
        assert result == struct.pack("<Id", expected_header, 3.14159)

    def test_encode_float_negative(self) -> None:
        result = self.encoder.encode(-1.5)
        expected_header = VariantType.FLOAT | HEADER_DATA_FLAG_64
        assert result == struct.pack("<Id", expected_header, -1.5)

    def test_encode_float_infinity(self) -> None:
        result = self.encoder.encode(float("inf"))
        expected_header = VariantType.FLOAT | HEADER_DATA_FLAG_64
        assert result == struct.pack("<Id", expected_header, float("inf"))


class TestVariantEncoderStrings:
    """Tests for VariantEncoder string encoding."""

    def setup_method(self) -> None:
        self.encoder = VariantEncoder()

    def test_encode_string_empty(self) -> None:
        result = self.encoder.encode("")
        # Empty string: header + 0 length + no padding
        assert result == struct.pack("<II", VariantType.STRING, 0)

    def test_encode_string_simple(self) -> None:
        result = self.encoder.encode("hello")
        # "hello" = 5 bytes, needs 3 bytes padding
        expected = struct.pack("<II", VariantType.STRING, 5) + b"hello\x00\x00\x00"
        assert result == expected

    def test_encode_string_no_padding(self) -> None:
        result = self.encoder.encode("abcd")
        # "abcd" = 4 bytes, no padding needed
        expected = struct.pack("<II", VariantType.STRING, 4) + b"abcd"
        assert result == expected

    def test_encode_string_padding_1(self) -> None:
        result = self.encoder.encode("abc")
        # "abc" = 3 bytes, needs 1 byte padding
        expected = struct.pack("<II", VariantType.STRING, 3) + b"abc\x00"
        assert result == expected

    def test_encode_string_padding_2(self) -> None:
        result = self.encoder.encode("ab")
        # "ab" = 2 bytes, needs 2 bytes padding
        expected = struct.pack("<II", VariantType.STRING, 2) + b"ab\x00\x00"
        assert result == expected

    def test_encode_string_padding_3(self) -> None:
        result = self.encoder.encode("a")
        # "a" = 1 byte, needs 3 bytes padding
        expected = struct.pack("<II", VariantType.STRING, 1) + b"a\x00\x00\x00"
        assert result == expected

    def test_encode_string_unicode(self) -> None:
        result = self.encoder.encode("héllo")
        utf8 = "héllo".encode("utf-8")  # 6 bytes
        pad_len = (4 - len(utf8) % 4) % 4
        expected = struct.pack("<II", VariantType.STRING, len(utf8)) + utf8 + b"\x00" * pad_len
        assert result == expected

    def test_encode_string_long(self) -> None:
        long_str = "x" * 1000
        result = self.encoder.encode(long_str)
        # 1000 bytes, no padding needed (1000 % 4 == 0)
        expected = struct.pack("<II", VariantType.STRING, 1000) + long_str.encode()
        assert result == expected


class TestVariantEncoderCollections:
    """Tests for VariantEncoder collection types."""

    def setup_method(self) -> None:
        self.encoder = VariantEncoder()

    def test_encode_array_empty(self) -> None:
        result = self.encoder.encode([])
        assert result == struct.pack("<II", VariantType.ARRAY, 0)

    def test_encode_array_integers(self) -> None:
        result = self.encoder.encode([1, 2, 3])
        # Header + count + 3 encoded ints
        expected = struct.pack("<II", VariantType.ARRAY, 3)
        expected += struct.pack("<Ii", VariantType.INT, 1)
        expected += struct.pack("<Ii", VariantType.INT, 2)
        expected += struct.pack("<Ii", VariantType.INT, 3)
        assert result == expected

    def test_encode_array_mixed(self) -> None:
        result = self.encoder.encode([1, "two", 3.0])
        # Count of 3 elements
        header = struct.pack("<II", VariantType.ARRAY, 3)
        int_part = struct.pack("<Ii", VariantType.INT, 1)
        str_part = struct.pack("<II", VariantType.STRING, 3) + b"two\x00"
        float_part = struct.pack("<Id", VariantType.FLOAT | HEADER_DATA_FLAG_64, 3.0)
        assert result == header + int_part + str_part + float_part

    def test_encode_array_nested(self) -> None:
        result = self.encoder.encode([[1], [2]])
        # Outer array with 2 inner arrays
        outer = struct.pack("<II", VariantType.ARRAY, 2)
        inner1 = struct.pack("<II", VariantType.ARRAY, 1) + struct.pack("<Ii", VariantType.INT, 1)
        inner2 = struct.pack("<II", VariantType.ARRAY, 1) + struct.pack("<Ii", VariantType.INT, 2)
        assert result == outer + inner1 + inner2

    def test_encode_tuple_as_array(self) -> None:
        result = self.encoder.encode((1, 2, 3))
        # Same as list encoding
        expected = struct.pack("<II", VariantType.ARRAY, 3)
        expected += struct.pack("<Ii", VariantType.INT, 1)
        expected += struct.pack("<Ii", VariantType.INT, 2)
        expected += struct.pack("<Ii", VariantType.INT, 3)
        assert result == expected

    def test_encode_dictionary_empty(self) -> None:
        result = self.encoder.encode({})
        assert result == struct.pack("<II", VariantType.DICTIONARY, 0)

    def test_encode_dictionary_simple(self) -> None:
        result = self.encoder.encode({"key": "value"})
        header = struct.pack("<II", VariantType.DICTIONARY, 1)
        key = struct.pack("<II", VariantType.STRING, 3) + b"key\x00"
        val = struct.pack("<II", VariantType.STRING, 5) + b"value\x00\x00\x00"
        assert result == header + key + val

    def test_encode_dictionary_nested(self) -> None:
        result = self.encoder.encode({"outer": {"inner": 1}})
        # Just verify it encodes without error and starts with dict header
        assert struct.unpack_from("<I", result, 0)[0] == VariantType.DICTIONARY

    def test_encode_packed_byte_array(self) -> None:
        result = self.encoder.encode(b"\x00\x01\x02")
        # 3 bytes, needs 1 byte padding
        expected = struct.pack("<II", VariantType.PACKED_BYTE_ARRAY, 3) + b"\x00\x01\x02\x00"
        assert result == expected

    def test_encode_packed_byte_array_no_padding(self) -> None:
        result = self.encoder.encode(b"\x00\x01\x02\x03")
        # 4 bytes, no padding needed
        expected = struct.pack("<II", VariantType.PACKED_BYTE_ARRAY, 4) + b"\x00\x01\x02\x03"
        assert result == expected


class TestVariantEncoderErrors:
    """Tests for VariantEncoder error handling."""

    def setup_method(self) -> None:
        self.encoder = VariantEncoder()

    def test_encode_unsupported_type(self) -> None:
        class CustomClass:
            pass

        with pytest.raises(TypeError) as exc:
            self.encoder.encode(CustomClass())
        assert "CustomClass" in str(exc.value)


class TestVariantDecoderPrimitives:
    """Tests for VariantDecoder primitive types."""

    def setup_method(self) -> None:
        self.decoder = VariantDecoder()

    def test_decode_nil(self) -> None:
        data = struct.pack("<I", VariantType.NIL)
        result, consumed = self.decoder.decode(data)
        assert result is None
        assert consumed == 4

    def test_decode_bool_true(self) -> None:
        data = struct.pack("<II", VariantType.BOOL, 1)
        result, consumed = self.decoder.decode(data)
        assert result is True
        assert consumed == 8

    def test_decode_bool_false(self) -> None:
        data = struct.pack("<II", VariantType.BOOL, 0)
        result, consumed = self.decoder.decode(data)
        assert result is False
        assert consumed == 8

    def test_decode_int_32bit(self) -> None:
        data = struct.pack("<Ii", VariantType.INT, 42)
        result, consumed = self.decoder.decode(data)
        assert result == 42
        assert consumed == 8

    def test_decode_int_32bit_negative(self) -> None:
        data = struct.pack("<Ii", VariantType.INT, -100)
        result, consumed = self.decoder.decode(data)
        assert result == -100
        assert consumed == 8

    def test_decode_int_64bit(self) -> None:
        header = VariantType.INT | HEADER_DATA_FLAG_64
        val = 9223372036854775807  # INT64_MAX
        data = struct.pack("<Iq", header, val)
        result, consumed = self.decoder.decode(data)
        assert result == val
        assert consumed == 12

    def test_decode_float_32bit(self) -> None:
        data = struct.pack("<If", VariantType.FLOAT, 3.14)
        result, consumed = self.decoder.decode(data)
        assert abs(result - 3.14) < 0.001
        assert consumed == 8

    def test_decode_float_64bit(self) -> None:
        header = VariantType.FLOAT | HEADER_DATA_FLAG_64
        data = struct.pack("<Id", header, 3.14159265358979)
        result, consumed = self.decoder.decode(data)
        assert abs(result - 3.14159265358979) < 1e-10
        assert consumed == 12

    def test_decode_string(self) -> None:
        data = struct.pack("<II", VariantType.STRING, 5) + b"hello\x00\x00\x00"
        result, consumed = self.decoder.decode(data)
        assert result == "hello"
        assert consumed == 16

    def test_decode_string_empty(self) -> None:
        data = struct.pack("<II", VariantType.STRING, 0)
        result, consumed = self.decoder.decode(data)
        assert result == ""
        assert consumed == 8

    def test_decode_string_unicode(self) -> None:
        utf8 = "héllo".encode("utf-8")  # 6 bytes
        pad_len = (4 - len(utf8) % 4) % 4
        data = struct.pack("<II", VariantType.STRING, len(utf8)) + utf8 + b"\x00" * pad_len
        result, consumed = self.decoder.decode(data)
        assert result == "héllo"


class TestVariantDecoderVectors:
    """Tests for VariantDecoder vector types."""

    def setup_method(self) -> None:
        self.decoder = VariantDecoder()

    def test_decode_vector2_32bit(self) -> None:
        data = struct.pack("<Iff", VariantType.VECTOR2, 1.0, 2.0)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "Vector2"
        assert result["x"] == 1.0
        assert result["y"] == 2.0
        assert consumed == 12

    def test_decode_vector2_64bit(self) -> None:
        header = VariantType.VECTOR2 | HEADER_DATA_FLAG_64
        data = struct.pack("<Idd", header, 1.5, 2.5)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "Vector2"
        assert result["x"] == 1.5
        assert result["y"] == 2.5
        assert consumed == 20

    def test_decode_vector2i(self) -> None:
        data = struct.pack("<Iii", VariantType.VECTOR2I, 10, 20)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "Vector2i"
        assert result["x"] == 10
        assert result["y"] == 20
        assert consumed == 12

    def test_decode_vector3_32bit(self) -> None:
        data = struct.pack("<Ifff", VariantType.VECTOR3, 1.0, 2.0, 3.0)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "Vector3"
        assert result["x"] == 1.0
        assert result["y"] == 2.0
        assert result["z"] == 3.0
        assert consumed == 16

    def test_decode_vector3i(self) -> None:
        data = struct.pack("<Iiii", VariantType.VECTOR3I, 1, 2, 3)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "Vector3i"
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3
        assert consumed == 16

    def test_decode_color(self) -> None:
        data = struct.pack("<Iffff", VariantType.COLOR, 1.0, 0.5, 0.0, 0.8)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "Color"
        assert result["r"] == 1.0
        assert result["g"] == 0.5
        assert result["b"] == 0.0
        assert result["a"] == pytest.approx(0.8)
        assert consumed == 20


class TestVariantDecoderCollections:
    """Tests for VariantDecoder collection types."""

    def setup_method(self) -> None:
        self.decoder = VariantDecoder()

    def test_decode_array_empty(self) -> None:
        data = struct.pack("<II", VariantType.ARRAY, 0)
        result, consumed = self.decoder.decode(data)
        assert result == []
        assert consumed == 8

    def test_decode_array_integers(self) -> None:
        data = struct.pack("<II", VariantType.ARRAY, 2)
        data += struct.pack("<Ii", VariantType.INT, 10)
        data += struct.pack("<Ii", VariantType.INT, 20)
        result, consumed = self.decoder.decode(data)
        assert result == [10, 20]

    def test_decode_array_nested(self) -> None:
        # [[1]]
        inner = struct.pack("<II", VariantType.ARRAY, 1) + struct.pack("<Ii", VariantType.INT, 1)
        data = struct.pack("<II", VariantType.ARRAY, 1) + inner
        result, consumed = self.decoder.decode(data)
        assert result == [[1]]

    def test_decode_dictionary_empty(self) -> None:
        data = struct.pack("<II", VariantType.DICTIONARY, 0)
        result, consumed = self.decoder.decode(data)
        assert result == {}
        assert consumed == 8

    def test_decode_dictionary_simple(self) -> None:
        data = struct.pack("<II", VariantType.DICTIONARY, 1)
        data += struct.pack("<II", VariantType.STRING, 3) + b"key\x00"
        data += struct.pack("<Ii", VariantType.INT, 42)
        result, consumed = self.decoder.decode(data)
        assert result == {"key": 42}

    def test_decode_packed_byte_array(self) -> None:
        data = struct.pack("<II", VariantType.PACKED_BYTE_ARRAY, 3) + b"\x01\x02\x03\x00"
        result, consumed = self.decoder.decode(data)
        assert result == b"\x01\x02\x03"

    def test_decode_packed_int32_array(self) -> None:
        data = struct.pack("<II", VariantType.PACKED_INT32_ARRAY, 3)
        data += struct.pack("<iii", 1, 2, 3)
        result, consumed = self.decoder.decode(data)
        assert result == [1, 2, 3]

    def test_decode_packed_int64_array(self) -> None:
        data = struct.pack("<II", VariantType.PACKED_INT64_ARRAY, 2)
        data += struct.pack("<qq", 9223372036854775807, -1)
        result, consumed = self.decoder.decode(data)
        assert result == [9223372036854775807, -1]

    def test_decode_packed_float32_array(self) -> None:
        data = struct.pack("<II", VariantType.PACKED_FLOAT32_ARRAY, 2)
        data += struct.pack("<ff", 1.5, 2.5)
        result, consumed = self.decoder.decode(data)
        assert len(result) == 2
        assert result[0] == pytest.approx(1.5)
        assert result[1] == pytest.approx(2.5)

    def test_decode_packed_float64_array(self) -> None:
        data = struct.pack("<II", VariantType.PACKED_FLOAT64_ARRAY, 2)
        data += struct.pack("<dd", 1.5, 2.5)
        result, consumed = self.decoder.decode(data)
        assert result == [1.5, 2.5]

    def test_decode_packed_string_array(self) -> None:
        data = struct.pack("<II", VariantType.PACKED_STRING_ARRAY, 2)
        data += struct.pack("<I", 2) + b"ab\x00\x00"  # "ab"
        data += struct.pack("<I", 2) + b"cd\x00\x00"  # "cd"
        result, consumed = self.decoder.decode(data)
        assert result == ["ab", "cd"]


class TestVariantDecoderSpecialTypes:
    """Tests for VariantDecoder special types."""

    def setup_method(self) -> None:
        self.decoder = VariantDecoder()

    def test_decode_string_name(self) -> None:
        # STRING_NAME uses same format as STRING
        data = struct.pack("<II", VariantType.STRING_NAME, 4) + b"test"
        result, consumed = self.decoder.decode(data)
        assert result == "test"

    def test_decode_rid(self) -> None:
        data = struct.pack("<IQ", VariantType.RID, 12345)
        result, consumed = self.decoder.decode(data)
        assert result["_type"] == "RID"
        assert result["id"] == 12345
        assert consumed == 12

    def test_decode_object_returns_none(self) -> None:
        data = struct.pack("<I", VariantType.OBJECT)
        result, consumed = self.decoder.decode(data)
        assert result is None
        assert consumed == 4


class TestVariantDecoderNodePath:
    """Tests for NODE_PATH decoding."""

    def setup_method(self) -> None:
        self.decoder = VariantDecoder()

    def test_decode_node_path_simple(self) -> None:
        # New format: namecount | 0x80000000, subnamecount, flags, then strings
        # Path: "Player" (1 name, 0 subnames, not absolute)
        data = struct.pack("<I", VariantType.NODE_PATH)
        data += struct.pack("<I", 1 | 0x80000000)  # namecount with new format flag
        data += struct.pack("<I", 0)  # subnamecount
        data += struct.pack("<I", 0)  # flags (not absolute)
        data += struct.pack("<I", 6) + b"Player\x00\x00"  # "Player" + padding
        result, consumed = self.decoder.decode(data)
        assert result == "Player"

    def test_decode_node_path_absolute(self) -> None:
        # Path: "/root/Main" (2 names, absolute)
        data = struct.pack("<I", VariantType.NODE_PATH)
        data += struct.pack("<I", 2 | 0x80000000)  # 2 names with new format
        data += struct.pack("<I", 0)  # 0 subnames
        data += struct.pack("<I", 1)  # flags = 1 (absolute)
        data += struct.pack("<I", 4) + b"root"  # "root"
        data += struct.pack("<I", 4) + b"Main"  # "Main"
        result, consumed = self.decoder.decode(data)
        assert result == "/root/Main"

    def test_decode_node_path_with_subnames(self) -> None:
        # Path: "Node:property" (1 name, 1 subname)
        data = struct.pack("<I", VariantType.NODE_PATH)
        data += struct.pack("<I", 1 | 0x80000000)  # 1 name
        data += struct.pack("<I", 1)  # 1 subname
        data += struct.pack("<I", 0)  # flags
        data += struct.pack("<I", 4) + b"Node"  # "Node"
        data += struct.pack("<I", 8) + b"property"  # "property"
        result, consumed = self.decoder.decode(data)
        assert result == "Node:property"

    def test_decode_node_path_old_format_raises(self) -> None:
        # Old format doesn't have 0x80000000 flag
        data = struct.pack("<I", VariantType.NODE_PATH)
        data += struct.pack("<I", 1)  # namecount without new format flag
        with pytest.raises(ValueError) as exc:
            self.decoder.decode(data)
        assert "Old NODE_PATH format" in str(exc.value)


class TestVariantDecoderErrors:
    """Tests for VariantDecoder error handling."""

    def setup_method(self) -> None:
        self.decoder = VariantDecoder()

    def test_decode_buffer_too_short(self) -> None:
        with pytest.raises(ValueError) as exc:
            self.decoder.decode(b"\x00\x00\x00")  # Only 3 bytes
        assert "Buffer too short" in str(exc.value)

    def test_decode_with_offset(self) -> None:
        # Put some garbage before the actual data
        prefix = b"\xff\xff\xff\xff"
        data = prefix + struct.pack("<Ii", VariantType.INT, 42)
        result, consumed = self.decoder.decode(data, offset=4)
        assert result == 42
        assert consumed == 8


class TestRoundTrip:
    """Tests for encode-then-decode round trips."""

    def setup_method(self) -> None:
        self.encoder = VariantEncoder()
        self.decoder = VariantDecoder()

    def _roundtrip(self, value):
        encoded = self.encoder.encode(value)
        decoded, _ = self.decoder.decode(encoded)
        return decoded

    def test_roundtrip_nil(self) -> None:
        assert self._roundtrip(None) is None

    def test_roundtrip_bool_true(self) -> None:
        assert self._roundtrip(True) is True

    def test_roundtrip_bool_false(self) -> None:
        assert self._roundtrip(False) is False

    def test_roundtrip_int_32bit(self) -> None:
        assert self._roundtrip(12345) == 12345

    def test_roundtrip_int_64bit(self) -> None:
        val = 9223372036854775807
        assert self._roundtrip(val) == val

    def test_roundtrip_float(self) -> None:
        assert self._roundtrip(3.14159) == pytest.approx(3.14159)

    def test_roundtrip_string(self) -> None:
        assert self._roundtrip("hello world") == "hello world"

    def test_roundtrip_string_unicode(self) -> None:
        assert self._roundtrip("héllo wörld") == "héllo wörld"

    def test_roundtrip_array(self) -> None:
        assert self._roundtrip([1, 2, 3]) == [1, 2, 3]

    def test_roundtrip_array_mixed(self) -> None:
        result = self._roundtrip([1, "two", 3.0])
        assert result[0] == 1
        assert result[1] == "two"
        assert result[2] == pytest.approx(3.0)

    def test_roundtrip_dictionary(self) -> None:
        assert self._roundtrip({"key": "value"}) == {"key": "value"}

    def test_roundtrip_dictionary_nested(self) -> None:
        data = {"outer": {"inner": 42}}
        assert self._roundtrip(data) == data

    def test_roundtrip_bytes(self) -> None:
        assert self._roundtrip(b"\x00\x01\x02\x03") == b"\x00\x01\x02\x03"

    def test_roundtrip_complex_nested(self) -> None:
        data = {
            "name": "test",
            "values": [1, 2, 3],
            "nested": {"a": True, "b": False},
        }
        assert self._roundtrip(data) == data


class TestMessageEncoding:
    """Tests for debugger protocol message encoding/decoding."""

    def test_encode_message_format(self) -> None:
        message = encode_message("automation:get_tree", 0, [])
        # Should start with 4-byte size prefix
        size = struct.unpack_from("<I", message, 0)[0]
        assert len(message) == 4 + size

    def test_encode_message_with_data(self) -> None:
        message = encode_message("automation:get_node", 1, ["/root/Main"])
        size = struct.unpack_from("<I", message, 0)[0]
        assert size > 0

    def test_decode_message_format(self) -> None:
        # Encode then decode (without size prefix)
        full_message = encode_message("automation:test", 123, ["data"])
        # Skip size prefix for decode_message
        data_without_prefix = full_message[4:]
        name, thread_id, data = decode_message(data_without_prefix)
        assert name == "automation:test"
        assert thread_id == 123
        assert data == ["data"]

    def test_decode_message_invalid_format(self) -> None:
        # Non-3-element array
        encoder = VariantEncoder()
        invalid = encoder.encode([1, 2])  # Only 2 elements
        with pytest.raises(ValueError) as exc:
            decode_message(invalid)
        assert "Invalid message format" in str(exc.value)


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_encode_variant(self) -> None:
        result = encode_variant(42)
        assert result == struct.pack("<Ii", VariantType.INT, 42)

    def test_decode_variant(self) -> None:
        data = struct.pack("<Ii", VariantType.INT, 42)
        result, consumed = decode_variant(data)
        assert result == 42
        assert consumed == 8
