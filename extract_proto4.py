#!/usr/bin/env python3
"""Extract proto definitions by finding class boundaries."""

import re
from pathlib import Path

def find_class_with_typename(js_content: str, type_name: str) -> str:
    """Find the class definition containing a typeName."""
    # Find the typeName
    type_pattern = f'typeName="{re.escape(type_name)}"'
    match = re.search(type_pattern, js_content)
    if not match:
        return None

    pos = match.start()

    # Search backwards for 'class X extends'
    search_back = 1000
    before = js_content[max(0, pos-search_back):pos]
    class_match = list(re.finditer(r'class\s+(\w+)\s+extends\s+\w+\.\w+\{', before))
    if class_match:
        class_start = max(0, pos-search_back) + class_match[-1].start()
        class_name = class_match[-1].group(1)
    else:
        return f"Could not find class start for {type_name}"

    # Now extract from class_start to find the fields
    class_content = js_content[class_start:pos+2000]

    # Find the fields definition
    fields_match = re.search(r'static fields=\w+\.\w+\.util\.newFieldList\(\(\)=>\[([^\]]*)\]\)', class_content)
    if fields_match:
        fields_raw = fields_match.group(1)
    else:
        # Try alternative pattern
        fields_match = re.search(r'fields=\w+\.util\.newFieldList\(\(\)=>\[([^\]]*)\]\)', class_content)
        if fields_match:
            fields_raw = fields_match.group(1)
        else:
            fields_raw = None

    return {
        'class_name': class_name,
        'type_name': type_name,
        'fields_raw': fields_raw,
        'context': class_content[:1500]  # First 1500 chars for debugging
    }

def parse_field_defs(fields_raw: str) -> list[dict]:
    """Parse field definitions from raw string."""
    if not fields_raw:
        return []

    fields = []
    # Match each field object
    for m in re.finditer(r'\{([^}]+)\}', fields_raw):
        field_str = m.group(1)
        field = {}

        # Parse properties
        props = [
            (r'no:(\d+)', 'no', int),
            (r'name:"([^"]+)"', 'name', str),
            (r'kind:"([^"]+)"', 'kind', str),
            (r'T:(\w+)', 'T', str),
            (r'opt:(!0|!1|true|false)', 'opt', lambda x: x in ('!0', 'true')),
            (r'repeated:(!0|!1|true|false)', 'repeated', lambda x: x in ('!0', 'true')),
            (r'K:(\d+)', 'K', int),
            (r'oneof:"([^"]+)"', 'oneof', str),
        ]

        for pattern, key, conv in props:
            pm = re.search(pattern, field_str)
            if pm:
                field[key] = conv(pm.group(1))

        if field.get('name'):
            fields.append(field)

    return sorted(fields, key=lambda f: f.get('no', 0))

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

        # Determine type
        if kind == 'scalar':
            try:
                proto_type = SCALAR_TYPES.get(int(t), f'scalar_{t}')
            except:
                proto_type = f'scalar_{t}'
        elif kind == 'message':
            proto_type = f'{t}'  # Class name reference
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

if __name__ == "__main__":
    js = Path("/tmp/cursor-index.js").read_text()

    targets = [
        "aiserver.v1.StreamUnifiedChatRequest",
        "aiserver.v1.StreamUnifiedChatResponse",
        "aiserver.v1.StreamChatToolformerContinueRequest",
        "aiserver.v1.StreamChatToolformerResponse",
        "aiserver.v1.StreamChatResponse",
    ]

    for tn in targets:
        print(f"\n{'='*70}")
        print(f"Extracting: {tn}")
        print('='*70)

        result = find_class_with_typename(js, tn)

        if isinstance(result, str):
            print(result)
            continue

        if not result:
            print("Not found")
            continue

        print(f"Class: {result['class_name']}")

        if result['fields_raw']:
            fields = parse_field_defs(result['fields_raw'])
            print(f"Fields found: {len(fields)}")
            print()
            print(format_proto(tn, fields))
        else:
            print("Fields not found directly")
            print("\nContext for debugging:")
            print(result['context'][:800])
