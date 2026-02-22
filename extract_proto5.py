#!/usr/bin/env python3
"""Extract proto definitions - fixed parsing."""

import re
from pathlib import Path

def extract_field_list(context: str) -> str:
    """Extract field list from context, handling nested brackets."""
    # Find start of newFieldList
    match = re.search(r'newFieldList\(\(\)=>\[', context)
    if not match:
        return None

    start = match.end()
    # Find matching closing bracket
    bracket_depth = 1
    pos = start
    while pos < len(context) and bracket_depth > 0:
        if context[pos] == '[':
            bracket_depth += 1
        elif context[pos] == ']':
            bracket_depth -= 1
        pos += 1

    return context[start:pos-1]

def parse_fields(fields_raw: str) -> list[dict]:
    """Parse field definitions."""
    if not fields_raw:
        return []

    fields = []
    # Match field objects, handling nested braces
    depth = 0
    start = None
    for i, c in enumerate(fields_raw):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                field_str = fields_raw[start+1:i]
                field = parse_single_field(field_str)
                if field.get('name'):
                    fields.append(field)
                start = None

    return sorted(fields, key=lambda f: f.get('no', 0))

def parse_single_field(field_str: str) -> dict:
    """Parse a single field definition."""
    field = {}
    props = [
        (r'no:(\d+)', 'no', int),
        (r'name:"([^"]+)"', 'name', str),
        (r'kind:"([^"]+)"', 'kind', str),
        (r'(?<![a-zA-Z])T:(\w+)', 'T', str),  # T: but not after letter
        (r'opt:(!0|!1|true|false)', 'opt', lambda x: x in ('!0', 'true')),
        (r'repeated:(!0|!1|true|false)', 'repeated', lambda x: x in ('!0', 'true')),
        (r'K:(\d+)', 'K', int),
        (r'oneof:"([^"]+)"', 'oneof', str),
    ]

    for pattern, key, conv in props:
        m = re.search(pattern, field_str)
        if m:
            field[key] = conv(m.group(1))

    return field

SCALAR_TYPES = {
    1: 'double', 2: 'float', 3: 'int64', 4: 'uint64', 5: 'int32',
    6: 'fixed64', 7: 'fixed32', 8: 'bool', 9: 'string', 12: 'bytes',
    13: 'uint32', 14: 'enum', 15: 'sfixed32', 16: 'sfixed64',
    17: 'sint32', 18: 'sint64',
}

def format_proto(type_name: str, fields: list[dict]) -> str:
    """Format as proto3."""
    msg = type_name.split('.')[-1]
    lines = [f'message {msg} {{']

    for f in fields:
        no = f.get('no', 0)
        name = f.get('name', '?')
        kind = f.get('kind', 'scalar')
        t = f.get('T', '9')

        if kind == 'scalar':
            try:
                proto_type = SCALAR_TYPES.get(int(t), f'scalar_{t}')
            except:
                proto_type = f'scalar_{t}'
        elif kind == 'message':
            proto_type = f'{t}'  # Class reference
        elif kind == 'enum':
            proto_type = f'enum_{t}'
        elif kind == 'map':
            k = SCALAR_TYPES.get(f.get('K', 9), 'string')
            proto_type = f'map<{k}, ?>'
        else:
            proto_type = f'{kind}_{t}'

        prefix = ''
        if f.get('repeated'):
            prefix = 'repeated '
        elif f.get('opt'):
            prefix = 'optional '

        oneof = f.get('oneof', '')
        oneof_comment = f'  // oneof {oneof}' if oneof else ''

        lines.append(f'  {prefix}{proto_type} {name} = {no};{oneof_comment}')

    lines.append('}')
    return '\n'.join(lines)

def find_message(js: str, type_name: str) -> dict:
    """Find a message definition."""
    pattern = f'typeName="{re.escape(type_name)}"'
    match = re.search(pattern, js)
    if not match:
        return None

    pos = match.start()
    # Get context - go back to find class, forward to get fields
    start = max(0, pos - 1000)
    end = min(len(js), pos + 5000)
    context = js[start:end]

    # Adjust for offset
    type_pos = pos - start

    # Find class name
    before = context[:type_pos]
    class_match = list(re.finditer(r'class\s+(\w+)\s+extends', before))
    class_name = class_match[-1].group(1) if class_match else "Unknown"

    # Extract fields
    after = context[type_pos:]
    fields_raw = extract_field_list(after)
    fields = parse_fields(fields_raw) if fields_raw else []

    return {
        'class_name': class_name,
        'type_name': type_name,
        'fields': fields,
        'fields_raw': fields_raw,
    }

if __name__ == "__main__":
    js = Path("/tmp/cursor-index.js").read_text()

    # Key messages
    targets = [
        "aiserver.v1.StreamUnifiedChatRequest",
        "aiserver.v1.StreamUnifiedChatResponse",
        "aiserver.v1.StreamChatToolformerContinueRequest",
        "aiserver.v1.StreamChatToolformerResponse",
        "aiserver.v1.StreamChatResponse",
    ]

    all_protos = []

    for tn in targets:
        print(f"\n{'='*70}")
        print(f"{tn}")
        print('='*70)

        result = find_message(js, tn)

        if not result:
            print("Not found")
            continue

        print(f"JS Class: {result['class_name']}")
        print(f"Fields: {len(result['fields'])}")

        if result['fields']:
            proto = format_proto(tn, result['fields'])
            print()
            print(proto)
            all_protos.append(proto)
        elif result['fields_raw']:
            print(f"Raw fields: {result['fields_raw'][:500]}...")
        else:
            print("No fields found")

    # Write combined proto file
    print("\n\n" + "="*70)
    print("Writing combined proto to cursor_api.proto")
    print("="*70)

    proto_content = '''syntax = "proto3";

package aiserver.v1;

// Extracted from Cursor CLI bundled JavaScript
// These are the key messages for the streaming chat API

'''
    proto_content += '\n\n'.join(all_protos)

    Path("cursor_api.proto").write_text(proto_content)
    print("Done!")
