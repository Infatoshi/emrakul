#!/usr/bin/env python3
"""Extract protobuf definitions from Cursor's bundled JavaScript - v2."""

import re
from pathlib import Path

def find_message_context(js_content: str, message_name: str, context_chars: int = 2000) -> list[str]:
    """Find context around a message name."""
    results = []
    pattern = re.compile(re.escape(message_name))
    for match in pattern.finditer(js_content):
        start = max(0, match.start() - 200)
        end = min(len(js_content), match.end() + context_chars)
        results.append(js_content[start:end])
    return results

def extract_field_lists(js_content: str) -> list[tuple[str, str]]:
    """Extract all newFieldList definitions with their context."""
    # Look for class definitions with typeName and fields
    # class X extends Message{static typeName="pkg.MsgName";static fields=...newFieldList(()=>[...])

    results = []

    # Find typeName assignments
    type_pattern = re.compile(r'static typeName="([^"]+)"')

    for type_match in type_pattern.finditer(js_content):
        type_name = type_match.group(1)
        start = type_match.start()

        # Look for fields definition after typeName
        search_region = js_content[start:start+5000]
        field_match = re.search(r'static fields=\w+\.\w+\.util\.newFieldList\(\(\)=>\[([^\]]*)\]', search_region)

        if field_match:
            fields_raw = field_match.group(1)
            results.append((type_name, fields_raw))

    return results

def parse_field_def(field_str: str) -> dict:
    """Parse a single field definition like {no:1,name:"foo",kind:"scalar",T:9}"""
    field = {}

    # Extract each property
    patterns = [
        (r'no:(\d+)', 'no', int),
        (r'name:"([^"]+)"', 'name', str),
        (r'kind:"([^"]+)"', 'kind', str),
        (r'T:(\d+)', 'T', int),
        (r'opt:(!0|!1|true|false)', 'optional', lambda x: x in ('!0', 'true')),
        (r'repeated:(!0|!1|true|false)', 'repeated', lambda x: x in ('!0', 'true')),
        (r'K:(\d+)', 'K', int),  # Map key type
    ]

    for pattern, key, converter in patterns:
        match = re.search(pattern, field_str)
        if match:
            field[key] = converter(match.group(1))

    return field

def proto_scalar_type(t: int) -> str:
    """Convert protobuf scalar type number."""
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
        12: "bytes",
        13: "uint32",
        14: "enum",
        15: "sfixed32",
        16: "sfixed64",
        17: "sint32",
        18: "sint64",
    }
    return types.get(t, f"type_{t}")

if __name__ == "__main__":
    print("=== Extracting Proto Definitions v2 ===\n")

    js_path = Path("/tmp/cursor-index.js")
    js_content = js_path.read_text()
    print(f"Loaded {len(js_content):,} bytes\n")

    # Extract all message definitions
    print("Extracting message definitions...")
    messages = extract_field_lists(js_content)
    print(f"Found {len(messages)} message definitions\n")

    # Filter for chat-related messages
    chat_messages = [(name, fields) for name, fields in messages
                     if any(x in name.lower() for x in ['chat', 'stream', 'unified', 'message', 'toolformer'])]

    print(f"Chat-related: {len(chat_messages)} messages\n")

    # Parse and display
    for type_name, fields_raw in sorted(chat_messages):
        print(f"\n=== {type_name} ===")

        # Split into individual field definitions
        field_defs = re.findall(r'\{[^}]+\}', fields_raw)

        for field_str in field_defs:
            field = parse_field_def(field_str)
            no = field.get('no', '?')
            name = field.get('name', '?')
            kind = field.get('kind', 'scalar')
            t = field.get('T', 0)

            type_str = proto_scalar_type(t) if kind == 'scalar' else f"{kind}({t})"
            prefix = "repeated " if field.get('repeated') else ("optional " if field.get('optional') else "")
            print(f"  {no}: {prefix}{type_str} {name}")

    # Also look specifically for StreamChat
    print("\n\n=== Searching for StreamChat specifics ===")
    contexts = find_message_context(js_content, "aiserver.v1.AiService")
    for i, ctx in enumerate(contexts[:3]):
        # Find method definitions
        methods = re.findall(r'(\w+):\{name:"([^"]+)"', ctx)
        if methods:
            print(f"\nContext {i+1} methods:")
            for method_key, method_name in methods:
                if 'stream' in method_key.lower() or 'chat' in method_name.lower():
                    print(f"  {method_key} -> {method_name}")
