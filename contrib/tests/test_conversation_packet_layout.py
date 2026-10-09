#!/usr/bin/env python3
"""Compare actual native packed structures with the original conversation packets."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


def declaration(text, name):
    start = text.index('struct '+name+'\n')
    opening = text.index('{', start)
    depth, end = 1, opening+1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    assert text[end] == ';'
    return text[start:end+1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-sanitizers', action='store_true', help='For compilers without sanitizer runtimes.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root/'docs/audit-data/campaign-simple-conversation-restoration.json').read_text('utf8'))
    store = (root/'src/server/game/Globals/ConversationDataStore.h').read_text('utf8')
    actor_header = (root/'src/server/game/Entities/Conversation/Conversation.h').read_text('utf8')
    native = '\n'.join([declaration(store,'ConversationActorTemplate'), declaration(store,'ConversationLineTemplate'), declaration(actor_header,'ConversationDynamicFieldActor')])
    cases = []
    actors = {int(row['Id']):row for row in registry['rows']['conversation_actor_template']}
    lines = {int(row['Id']):row for row in registry['rows']['conversation_line_template']}
    chain_registry = json.loads((root/'docs/audit-data/campaign-conversation-chain-restoration.json').read_text('utf8'))
    actors.update({int(row['Id']):row for row in chain_registry['rows']['conversation_actor_template']})
    lines.update({int(row['Id']):row for row in chain_registry['rows']['conversation_line_template']})
    source_pairs = [(candidate['source_actors'][0],candidate['source_line']) for candidate in registry['source']]
    for candidate in chain_registry['source']:
        indexed = {int(actor['id']):actor for actor in candidate['actors']}
        source_pairs.extend((indexed[int(line['unk2'])],line) for line in candidate['lines'])
    for old_actor,old_line in source_pairs:
        actor = actors[int(old_actor['actorId'])]
        line = lines[int(old_line['id'])]
        actor_packet = struct.pack('<6I', *(int(old_actor[key]) for key in ('actorId','creatureId','displayId','unk1','unk2','unk3')))
        line_packet = struct.pack('<4I', *(int(old_line[key]) for key in ('id','textId','unk1','unk2')))
        def array(packet):
            return '{'+','.join(map(str,packet))+'}'
        cases.append('''{
            ConversationDynamicFieldActor actor;
            actor.ActorTemplate = {%s,%s,%s}; actor.Type = ConversationDynamicFieldActor::CreatureActor;
            ConversationLineTemplate line = {%s,%s,%s,%s,%s,0};
            unsigned char expectedActor[24] = %s, expectedLine[16] = %s;
            if (std::memcmp(&actor,expectedActor,24) || std::memcmp(&line,expectedLine,16)) return 1;
        }''' % (actor['Id'],actor['CreatureId'],actor['CreatureModelId'],line['Id'],line['StartTime'],line['UiCameraID'],line['ActorIdx'],line['Flags'],array(actor_packet),array(line_packet)))
    assert len(cases) == 22
    gunpowder = json.loads((root/'docs/audit-data/campaign-gunpowder-conversation-restoration.json').read_text('utf8'))
    actor = gunpowder['rows']['conversation_actor_template'][0]
    original_actor = gunpowder['source']['conversation_actor'][0]
    actor_packet = struct.pack('<6I', *(int(original_actor[k]) for k in ('actorId','creatureId','displayId','unk1','unk2','unk3')))
    for original_line,line in zip(gunpowder['source']['conversation_data'],gunpowder['rows']['conversation_line_template']):
        line_packet = struct.pack('<4I', *(int(original_line[k]) for k in ('id','textId','unk1','unk2')))
        cases.append('{ ConversationDynamicFieldActor actor; actor.ActorTemplate={%s,%s,%s}; actor.Type=ConversationDynamicFieldActor::CreatureActor; ConversationLineTemplate line={%s,%s,%s,%s,%s,%s}; unsigned char a[24]=%s,l[16]=%s; if(std::memcmp(&actor,a,24)||std::memcmp(&line,l,16)) return 1; }' % (actor['Id'],actor['CreatureId'],actor['CreatureModelId'],line['Id'],line['StartTime'],line['UiCameraID'],line['ActorIdx'],line['Flags'],line['Padding'],array(actor_packet),array(line_packet)))
    nearest = json.loads((root/'docs/audit-data/campaign-nearest-conversation-restoration.json').read_text('utf8'))
    nearest_lines = {int(row['Id']):row for row in nearest['rows']['conversation_line_template']}
    for candidate in nearest['source']:
        for old_line in candidate['lines']:
            line = nearest_lines[int(old_line['id'])]
            packet = struct.pack('<4I', *(int(old_line[key]) for key in ('id','textId','unk1','unk2')))
            cases.append('{ ConversationLineTemplate line = {%s,%s,%s,%s,%s,0}; unsigned char expected[16] = %s; if (std::memcmp(&line,expected,16)) return 1; }' % (line['Id'],line['StartTime'],line['UiCameraID'],line['ActorIdx'],line['Flags'],array(packet)))
    assert len(cases) == 64
    packed = json.loads((root/'docs/audit-data/campaign-packed-conversation-restoration.json').read_text('utf8'))
    timing=json.loads((root/'docs/audit-data/campaign-source-timing-conversations.json').read_text('utf8'))
    packed['source']+=timing['source'];packed['rows']['conversation_line_template']+=timing['rows']['conversation_line_template']
    packed_lines = {int(row['Id']):row for row in packed['rows']['conversation_line_template']}
    for candidate in packed['source']:
        for old_line in candidate['lines']:
            line = packed_lines[int(old_line['id'])]
            packet = struct.pack('<4I', *(int(old_line[key]) for key in ('id','textId','unk1','unk2')))
            cases.append('{ ConversationLineTemplate line = {%s,%s,%s,%s,%s,%s}; unsigned char expected[16] = %s; if (std::memcmp(&line,expected,16)) return 1; }' % (line['Id'],line['StartTime'],line['UiCameraID'],line['ActorIdx'],line['Flags'],line['Padding'],array(packet)))
    assert len(cases) == 73
    source_actors=json.loads((root/'docs/audit-data/campaign-source-actor-conversations.json').read_text('utf8'))
    restored_lines={int(row['Id']):row for row in source_actors['rows']['conversation_line_template']}
    for candidate in source_actors['source']:
        for old_line in candidate['lines']:
            line=restored_lines[int(old_line['id'])]
            packet=struct.pack('<4I', *(int(old_line[key]) for key in ('id','textId','unk1','unk2')))
            cases.append('{ ConversationLineTemplate line = {%s,%s,%s,%s,%s,%s}; unsigned char expected[16] = %s; if (std::memcmp(&line,expected,16)) return 1; }' % (line['Id'],line['StartTime'],line['UiCameraID'],line['ActorIdx'],line['Flags'],line['Padding'],array(packet)))
        for old_actor in candidate['actors']:
            packet=struct.pack('<6I', *(int(old_actor[key]) for key in ('actorId','creatureId','displayId','unk1','unk2','unk3')))
            cases.append('{ ConversationDynamicFieldActor actor; actor.ActorTemplate={%s,%s,%s}; actor.Type=ConversationDynamicFieldActor::CreatureActor; unsigned char expected[24]=%s; if (std::memcmp(&actor,expected,24)) return 1; }' % (old_actor['actorId'],old_actor['creatureId'],old_actor['displayId'],array(packet)))
    assert len(cases) == 82

    harness = '''#include <cstdint>
#include <cstddef>
#include <cstring>
#include <iostream>
using uint8=std::uint8_t; using uint16=std::uint16_t; using uint32=std::uint32_t;
struct ObjectGuid { std::uint64_t low, high; bool IsEmpty() const { return !low && !high; } };
#pragma pack(push,1)
'''+native+'''
#pragma pack(pop)
static_assert(sizeof(ConversationDynamicFieldActor)==24);
static_assert(sizeof(ConversationLineTemplate)==16);
static_assert(offsetof(ConversationDynamicFieldActor,Type)==16);
static_assert(offsetof(ConversationDynamicFieldActor,Padding)==20);
static_assert(offsetof(ConversationLineTemplate,ActorIdx)==12);
static_assert(offsetof(ConversationLineTemplate,Flags)==13);
static_assert(offsetof(ConversationLineTemplate,Padding)==14);
int main() {
'''+ '\n'.join(cases)+'''
std::cout << "PASS: seventy-nine original line packets and twenty-seven actor packets match actual native packed structures byte for byte\\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp)/'conversation.cpp', Path(tmp)/'conversation'
        cpp.write_text(harness,encoding='utf8')
        flags = [] if args.no_sanitizers else ['-fsanitize=address,undefined','-fno-sanitize-recover=all']
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',*flags,'-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__ == '__main__':
    main()
