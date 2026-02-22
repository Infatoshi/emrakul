#!/usr/bin/env python3
"""Debug the protobuf encoding."""

def decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    """Decode varint, return (value, new_offset)."""
    value = 0
    shift = 0
    while offset < len(data):
        b = data[offset]
        value |= (b & 0x7f) << shift
        offset += 1
        if not (b & 0x80):
            break
        shift += 7
    return value, offset

def parse_proto(data: bytes, indent: int = 0) -> None:
    """Parse and print protobuf structure."""
    offset = 0
    prefix = "  " * indent

    while offset < len(data):
        if offset >= len(data):
            break

        tag_byte = data[offset]
        field_num = tag_byte >> 3
        wire_type = tag_byte & 0x07
        offset += 1

        print(f"{prefix}Field {field_num}, Wire type {wire_type}", end="")

        if wire_type == 0:  # Varint
            value, offset = decode_varint(data, offset)
            print(f" = {value}")
        elif wire_type == 2:  # Length-delimited
            length, offset = decode_varint(data, offset)
            content = data[offset:offset+length]
            offset += length
            # Try to decode as string
            try:
                s = content.decode('utf-8')
                if s.isprintable():
                    print(f' = "{s}"')
                else:
                    print(f" = bytes({length}): {content[:50].hex()}...")
                    # Try parsing as nested message
                    print(f"{prefix}  [Nested message:]")
                    parse_proto(content, indent + 2)
            except:
                print(f" = bytes({length}): {content[:50].hex()}...")
                # Try parsing as nested message
                print(f"{prefix}  [Nested message:]")
                try:
                    parse_proto(content, indent + 2)
                except:
                    pass
        elif wire_type == 5:  # 32-bit fixed
            value = int.from_bytes(data[offset:offset+4], 'little')
            offset += 4
            print(f" = {value} (fixed32)")
        elif wire_type == 1:  # 64-bit fixed
            value = int.from_bytes(data[offset:offset+8], 'little')
            offset += 8
            print(f" = {value} (fixed64)")
        else:
            print(f" = INVALID WIRE TYPE!")
            break

# Test request from the file
hex_data = "00000000420a080a047465737410022a090a076770742d352e32b00101ba012463663536343936392d353736372d346438322d623561322d386639646533326532346566e80201"
data = bytes.fromhex(hex_data)

print("=== Connect frame ===")
print(f"Flags: {data[0]}")
print(f"Length: {int.from_bytes(data[1:5], 'big')}")
print()

print("=== Protobuf content ===")
proto_data = data[5:]
print(f"Total bytes: {len(proto_data)}")
print(f"Hex: {proto_data.hex()}")
print()

parse_proto(proto_data)
