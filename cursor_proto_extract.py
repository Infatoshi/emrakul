#!/usr/bin/env python3
"""Extract Cursor API protobuf definitions."""

import re
from pathlib import Path

SCALAR_TYPES = {
    1: 'double', 2: 'float', 3: 'int64', 4: 'uint64', 5: 'int32',
    6: 'fixed64', 7: 'fixed32', 8: 'bool', 9: 'string', 12: 'bytes',
    13: 'uint32', 14: 'enum', 15: 'sfixed32', 16: 'sfixed64',
    17: 'sint32', 18: 'sint64',
}

def extract_messages(js_content: str, type_names: list[str]) -> dict:
    """Extract message definitions from bundled JS."""
    results = {}

    for type_name in type_names:
        # Find typeName="..."
        pattern = f'typeName="{re.escape(type_name)}"'
        match = re.search(pattern, js_content)
        if not match:
            continue

        pos = match.start()
        after = js_content[pos:pos+3000]

        # Find fields=...newFieldList((()=>[...]))
        fl_match = re.search(r'fields=\w+\.\w+\.util\.newFieldList\(\(\(\)=>\[([^\]]+)\]\)\)', after)
        if not fl_match:
            # Try alternative pattern
            fl_match = re.search(r'newFieldList\(\(\(\)=>\[([^\]]+)\]\)\)', after)

        if fl_match:
            fields_raw = fl_match.group(1)
            fields = parse_fields(fields_raw)
            results[type_name] = fields

    return results

def parse_fields(fields_raw: str) -> list[dict]:
    """Parse field definitions from the raw array content."""
    fields = []

    # Split by field objects - match {no:...}
    for m in re.finditer(r'\{no:(\d+)[^}]+\}', fields_raw):
        field_str = m.group(0)
        field = {'no': int(m.group(1))}

        # Extract other properties
        name_m = re.search(r'name:"([^"]+)"', field_str)
        if name_m:
            field['name'] = name_m.group(1)

        kind_m = re.search(r'kind:"([^"]+)"', field_str)
        if kind_m:
            field['kind'] = kind_m.group(1)

        t_m = re.search(r',T:(\w+)', field_str)
        if t_m:
            field['T'] = t_m.group(1)

        if 'opt:!0' in field_str or 'opt:true' in field_str:
            field['optional'] = True

        if 'repeated:!0' in field_str or 'repeated:true' in field_str:
            field['repeated'] = True

        oneof_m = re.search(r'oneof:"([^"]+)"', field_str)
        if oneof_m:
            field['oneof'] = oneof_m.group(1)

        if field.get('name'):
            fields.append(field)

    return sorted(fields, key=lambda f: f['no'])

def format_proto_message(type_name: str, fields: list[dict]) -> str:
    """Format as proto3 message."""
    msg_name = type_name.split('.')[-1]
    lines = [f'message {msg_name} {{']

    # Group by oneof
    oneofs = {}
    regular_fields = []
    for f in fields:
        if f.get('oneof'):
            oneofs.setdefault(f['oneof'], []).append(f)
        else:
            regular_fields.append(f)

    # Output regular fields
    for f in regular_fields:
        line = format_field(f)
        lines.append(f'  {line}')

    # Output oneofs
    for oneof_name, oneof_fields in oneofs.items():
        lines.append(f'  oneof {oneof_name} {{')
        for f in oneof_fields:
            line = format_field(f, in_oneof=True)
            lines.append(f'    {line}')
        lines.append('  }')

    lines.append('}')
    return '\n'.join(lines)

def format_field(f: dict, in_oneof: bool = False) -> str:
    """Format a single field."""
    no = f['no']
    name = f['name']
    kind = f.get('kind', 'scalar')
    t = f.get('T', '9')

    if kind == 'scalar':
        try:
            proto_type = SCALAR_TYPES.get(int(t), f'unknown_{t}')
        except:
            proto_type = f'unknown_{t}'
    elif kind == 'message':
        proto_type = t  # Reference to another message class
    elif kind == 'enum':
        proto_type = t
    else:
        proto_type = f'{kind}_{t}'

    prefix = ''
    if not in_oneof:
        if f.get('repeated'):
            prefix = 'repeated '
        elif f.get('optional'):
            prefix = 'optional '

    return f'{prefix}{proto_type} {name} = {no};'

def main():
    js = Path("/tmp/cursor-index.js").read_text()

    # Key streaming chat messages
    targets = [
        "aiserver.v1.StreamUnifiedChatRequest",
        "aiserver.v1.StreamUnifiedChatResponse",
        "aiserver.v1.StreamChatToolformerContinueRequest",
        "aiserver.v1.StreamChatToolformerResponse",
        "aiserver.v1.StreamChatToolformerResponse.Output",
        "aiserver.v1.StreamChatToolformerResponse.Thought",
        "aiserver.v1.StreamChatToolformerResponse.ToolAction",
        "aiserver.v1.StreamChatResponse",
        "aiserver.v1.StreamChatContextRequest",
    ]

    print("="*70)
    print("CURSOR API PROTO EXTRACTION")
    print("="*70)

    results = extract_messages(js, targets)

    all_protos = []
    for type_name in targets:
        if type_name in results:
            fields = results[type_name]
            print(f"\n{type_name}: {len(fields)} fields")
            proto = format_proto_message(type_name, fields)
            print(proto)
            all_protos.append(proto)
        else:
            # Manual extraction fallback
            pattern = f'typeName="{re.escape(type_name)}"'
            match = re.search(pattern, js)
            if match:
                pos = match.start()
                after = js[pos:pos+1500]
                # Direct extract from visible pattern
                fields_m = re.search(r'\[(\{no:[^]]+)\]', after)
                if fields_m:
                    fields_raw = fields_m.group(1)
                    fields = parse_fields(fields_raw)
                    if fields:
                        print(f"\n{type_name}: {len(fields)} fields (fallback)")
                        proto = format_proto_message(type_name, fields)
                        print(proto)
                        all_protos.append(proto)
                    else:
                        print(f"\n{type_name}: no fields parsed from: {fields_raw[:200]}...")
                else:
                    print(f"\n{type_name}: typeName found but no fields pattern")
            else:
                print(f"\n{type_name}: not found")

    # Write to file
    output_path = Path("cursor_api.proto")
    proto_content = '''syntax = "proto3";

package aiserver.v1;

// Cursor API Proto Definitions
// Extracted from Cursor CLI JavaScript bundle
// For direct API access to Claude 4.5 Opus, GPT-5.2 Codex, etc.

'''
    proto_content += '\n\n'.join(all_protos)

    output_path.write_text(proto_content)
    print(f"\n\nWritten to {output_path}")

if __name__ == "__main__":
    main()
