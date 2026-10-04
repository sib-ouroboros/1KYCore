#!/usr/bin/env python3
"""Compare actual native packed structures with the original conversation packets."""
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
    root = Path(__file__).resolve().parents[2]
    registry = json.loads((root/'docs/audit-data/campaign-simple-conversation-restoration.json').read_text('utf8'))
    store = (root/'src/server/game/Globals/ConversationDataStore.h').read_text('utf8')
    actor_header = (root/'src/server/game/Entities/Conversation/Conversation.h').read_text('utf8')
    native = '\n'.join([declaration(store,'ConversationActorTemplate'), declaration(store,'ConversationLineTemplate'), declaration(actor_header,'ConversationDynamicFieldActor')])
    cases = []
    actors = {int(row['Id']):row for row in registry['rows']['conversation_actor_template']}
    lines = {int(row['Id']):row for row in registry['rows']['conversation_line_template']}
    for candidate in registry['source']:
        old_actor = candidate['source_actors'][0]
        old_line = candidate['source_line']
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
    assert len(cases) == 13
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
std::cout << "PASS: thirteen original actor/line packets match actual native packed structures byte for byte\\n";
}
'''
    with tempfile.TemporaryDirectory() as tmp:
        cpp, exe = Path(tmp)/'conversation.cpp', Path(tmp)/'conversation'
        cpp.write_text(harness,encoding='utf8')
        subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-sanitize-recover=all','-g',str(cpp),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)


if __name__ == '__main__':
    main()
