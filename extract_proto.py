#!/usr/bin/env python3
"""Extract protobuf definitions from Cursor's bundled JavaScript."""

import re
import json
from pathlib import Path

def extract_proto_fields(js_content: str) -> dict:
    """Extract proto message field definitions from bundled JS."""

    # Pattern to find message class definitions with fields
    # Format: class MessageName extends ... static fields=o.C.util.newFieldList(()=>[{no:1,name:"field",...}])

    messages = {}

    # Find all message names and their field lists
    # Pattern: typeName="package.MessageName"...static fields=...newFieldList(()=>[...])
    pattern = r'typeName="([^"]+)"[^}]*?static fields=\w+\.\w+\.util\.newFieldList\(\(\)=>\[([^\]]+)\]'

    for match in re.finditer(pattern, js_content):
        type_name = match.group(1)
        fields_raw = match.group(2)

        # Parse individual fields
        # Format: {no:1,name:"fieldName",kind:"scalar",T:9}
        field_pattern = r'\{([^}]+)\}'
        fields = []

        for field_match in re.finditer(field_pattern, fields_raw):
            field_def = field_match.group(1)
            field = {}

            # Extract field properties
            for prop in ['no', 'name', 'kind', 'T', 'opt', 'repeated']:
                prop_pattern = rf'{prop}:([^,}}]+)'
                prop_match = re.search(prop_pattern, field_def)
                if prop_match:
                    value = prop_match.group(1).strip('"\'')
                    # Convert numeric values
                    if value.isdigit():
                        value = int(value)
                    elif value == 'true':
                        value = True
                    elif value == 'false':
                        value = False
                    field[prop] = value

            if field:
                fields.append(field)

        if fields:
            messages[type_name] = fields

    return messages

def proto_type_to_name(t: int) -> str:
    """Convert protobuf type number to name."""
    # Protobuf wire types / scalar types
    types = {
        1: "double",
        2: "float",
        3: "int64",
        4: "uint64",
        5: "int32",
        6: "fixed64",
        7: "fixed32",
        8: "bool",
        9: "string",
        10: "group",
        11: "message",
        12: "bytes",
        13: "uint32",
        14: "enum",
        15: "sfixed32",
        16: "sfixed64",
        17: "sint32",
        18: "sint64",
    }
    return types.get(t, f"unknown({t})")

def format_proto(messages: dict) -> str:
    """Format extracted messages as .proto file."""
    output = []
    output.append('syntax = "proto3";')
    output.append('')
    output.append('package aiserver.v1;')
    output.append('')

    # Group by package
    for type_name, fields in sorted(messages.items()):
        # Extract message name from full type
        parts = type_name.split('.')
        msg_name = parts[-1]

        output.append(f'message {msg_name} {{')

        for field in sorted(fields, key=lambda x: x.get('no', 0)):
            no = field.get('no', 0)
            name = field.get('name', 'unknown')
            kind = field.get('kind', 'scalar')
            t = field.get('T', 9)
            opt = field.get('opt', False)
            repeated = field.get('repeated', False)

            # Determine type
            if kind == 'scalar':
                proto_type = proto_type_to_name(t)
            elif kind == 'message':
                proto_type = f"message_type_{t}"
            elif kind == 'enum':
                proto_type = f"enum_type_{t}"
            else:
                proto_type = f"{kind}_{t}"

            # Build field line
            prefix = "repeated " if repeated else ("optional " if opt else "")
            output.append(f'  {prefix}{proto_type} {name} = {no};')

        output.append('}')
        output.append('')

    return '\n'.join(output)

def find_streaming_services(js_content: str) -> list:
    """Find streaming service definitions."""
    # Pattern for service method definitions
    # streamChat:{name:"StreamChat",I:StreamChatRequest,O:StreamChatResponse,...}
    pattern = r'(\w+):\{name:"([^"]+)",I:(\w+),O:(\w+)'

    services = []
    for match in re.finditer(pattern, js_content):
        services.append({
            'method_key': match.group(1),
            'method_name': match.group(2),
            'input_type': match.group(3),
            'output_type': match.group(4),
        })

    return services

if __name__ == "__main__":
    print("=== Extracting Proto Definitions from Cursor ===\n")

    js_path = Path("/tmp/cursor-index.js")
    if not js_path.exists():
        print("Error: /tmp/cursor-index.js not found")
        print("Copy from: ~/.local/share/cursor-agent/versions/*/index.js")
        exit(1)

    js_content = js_path.read_text()
    print(f"Loaded {len(js_content):,} bytes of JavaScript\n")

    # Extract messages
    print("Extracting proto messages...")
    messages = extract_proto_fields(js_content)
    print(f"Found {len(messages)} message types\n")

    # Filter for interesting messages
    chat_messages = {k: v for k, v in messages.items() if 'Chat' in k or 'Stream' in k}
    print(f"Chat/Stream related: {len(chat_messages)} messages\n")

    # Print chat-related messages
    for name, fields in sorted(chat_messages.items()):
        print(f"\n{name}:")
        for f in fields:
            print(f"  {f.get('no', '?')}: {f.get('name', '?')} ({f.get('kind', '?')}, T={f.get('T', '?')})")

    # Find streaming services
    print("\n\n=== Streaming Services ===")
    services = find_streaming_services(js_content)
    stream_services = [s for s in services if 'stream' in s['method_key'].lower()]
    for s in stream_services[:20]:
        print(f"  {s['method_name']}: {s['input_type']} -> {s['output_type']}")

    # Save full proto extraction
    print("\n\nSaving full proto to /tmp/cursor.proto...")
    proto_content = format_proto(messages)
    Path("/tmp/cursor.proto").write_text(proto_content)
    print("Done!")
