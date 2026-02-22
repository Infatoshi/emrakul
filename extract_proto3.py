#!/usr/bin/env python3
"""Extract specific proto message definitions from Cursor JS."""

import re
from pathlib import Path

def extract_message_def(js_content: str, type_name: str) -> str:
    """Extract the class definition for a specific typeName."""
    # Find the position of the typeName
    pattern = f'typeName="{re.escape(type_name)}"'
    match = re.search(pattern, js_content)
    if not match:
        return None

    # Search backwards to find 'class' keyword
    pos = match.start()
    search_start = max(0, pos - 500)
    before = js_content[search_start:pos]

    # Find the class definition
    class_match = re.search(r'class\s+(\w+)\s+extends', before)
    if class_match:
        class_name = class_match.group(1)
    else:
        class_name = "Unknown"

    # Search forward for fields
    search_end = min(len(js_content), pos + 3000)
    after = js_content[pos:search_end]

    # Find the fields definition
    fields_match = re.search(r'static fields=\w+\.\w+\.util\.newFieldList\(\(\)=>\[([^\]]*)\]', after)
    if fields_match:
        fields_raw = fields_match.group(1)
    else:
        fields_raw = "(no fields found)"

    return f"class {class_name}:\n  typeName: {type_name}\n  fields: {fields_raw}"

def parse_fields(fields_raw: str) -> list[dict]:
    """Parse field definitions."""
    fields = []
    for field_match in re.finditer(r'\{([^}]+)\}', fields_raw):
        field_str = field_match.group(1)
        field = {}

        # Extract properties
        for pattern, key, conv in [
            (r'no:(\d+)', 'no', int),
            (r'name:"([^"]+)"', 'name', str),
            (r'kind:"([^"]+)"', 'kind', str),
            (r'T:(\w+)', 'T', str),  # Keep as string for now
            (r'opt:(!0|!1)', 'optional', lambda x: x == '!0'),
            (r'repeated:(!0|!1)', 'repeated', lambda x: x == '!0'),
            (r'K:(\d+)', 'K', int),
            (r'V:\{([^}]+)\}', 'V', str),
        ]:
            m = re.search(pattern, field_str)
            if m:
                field[key] = conv(m.group(1))

        if field.get('name'):
            fields.append(field)

    return sorted(fields, key=lambda x: x.get('no', 0))

PROTO_TYPES = {
    '1': 'double', '2': 'float', '3': 'int64', '4': 'uint64', '5': 'int32',
    '6': 'fixed64', '7': 'fixed32', '8': 'bool', '9': 'string',
    '12': 'bytes', '13': 'uint32', '14': 'enum', '15': 'sfixed32',
    '16': 'sfixed64', '17': 'sint32', '18': 'sint64',
}

def format_proto_message(type_name: str, fields: list[dict]) -> str:
    """Format as proto3 message."""
    msg_name = type_name.split('.')[-1]
    lines = [f'message {msg_name} {{']

    for f in fields:
        no = f.get('no', 0)
        name = f.get('name', 'unknown')
        kind = f.get('kind', 'scalar')
        t = str(f.get('T', '9'))

        if kind == 'scalar':
            proto_type = PROTO_TYPES.get(t, f'type{t}')
        elif kind == 'message':
            proto_type = f'Message_{t}'  # Referenced message type
        elif kind == 'enum':
            proto_type = f'Enum_{t}'
        elif kind == 'map':
            k_type = PROTO_TYPES.get(str(f.get('K', 9)), 'string')
            v_info = f.get('V', '')
            proto_type = f'map<{k_type}, value>'
        else:
            proto_type = f'{kind}_{t}'

        prefix = ''
        if f.get('repeated'):
            prefix = 'repeated '
        elif f.get('optional'):
            prefix = 'optional '

        lines.append(f'  {prefix}{proto_type} {name} = {no};')

    lines.append('}')
    return '\n'.join(lines)

if __name__ == "__main__":
    js_content = Path("/tmp/cursor-index.js").read_text()

    # Key messages to extract
    messages_to_extract = [
        "aiserver.v1.StreamUnifiedChatRequest",
        "aiserver.v1.StreamUnifiedChatResponse",
        "aiserver.v1.StreamChatToolformerContinueRequest",
        "aiserver.v1.StreamChatToolformerResponse",
        "aiserver.v1.StreamChatResponse",
        "aiserver.v1.ChatMessage",
        "aiserver.v1.Message",
    ]

    print("=== Cursor Proto Message Definitions ===\n")

    for type_name in messages_to_extract:
        print(f"\n{'='*60}")
        print(f"Looking for: {type_name}")

        # Find typeName in JS
        pattern = f'typeName="{re.escape(type_name)}"'
        match = re.search(pattern, js_content)

        if not match:
            print(f"  NOT FOUND")
            continue

        # Get surrounding context
        pos = match.start()
        context_start = max(0, pos - 300)
        context_end = min(len(js_content), pos + 2000)
        context = js_content[context_start:context_end]

        # Find fields
        fields_match = re.search(r'static fields=\w+\.\w+\.util\.newFieldList\(\(\)=>\[([^\]]*)\]', context)

        if fields_match:
            fields_raw = fields_match.group(1)
            fields = parse_fields(fields_raw)

            print(f"\n{format_proto_message(type_name, fields)}")
        else:
            print(f"  Fields not found in context")

    # Also find what messages are referenced
    print("\n\n=== Finding Message Type References ===")
    # Look for T:X where X is a class reference
    t_refs = re.findall(r'kind:"message",T:(\w+)', js_content)
    unique_refs = sorted(set(t_refs))[:30]
    print(f"Message type references (T:X): {unique_refs}")
