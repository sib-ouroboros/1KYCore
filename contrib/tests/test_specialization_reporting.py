#!/usr/bin/env python3
"""Compile the actual reporting function with small Player/DB2 test doubles.

This tests lookup and validation behavior without booting a realm or loading DB2 files.
Run with Python 3 and a C++17 compiler available as CXX (defaults to c++).
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    source = (root / 'src/server/game/Entities/Player/PlayerCharacterSetup.cpp').read_text(encoding='utf-8')
    match = re.search(r'^uint32 PlayerCharacterSetup::FindPlayerTalentType\(Player\* player\)\n\{.*?^\}', source, re.M | re.S)
    if not match:
        raise SystemExit('Reporting function was moved or renamed; update this regression harness.')
    defines = (root / 'src/server/game/Miscellaneous/SharedDefines.h').read_text(encoding='utf-8')
    maximum = re.search(r'^#define MAX_SPECIALIZATIONS\s+(\d+)', defines, re.M)
    if not maximum:
        raise SystemExit('MAX_SPECIALIZATIONS not found')
    harness = r'''
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <unordered_map>
using uint32 = std::uint32_t;
using uint8 = std::uint8_t;
struct Player
{
    uint32 specId;
    uint8 classId;
    uint32 GetSpecializationId() const { return specId; }
    uint8 getClass() const { return classId; }
};
struct ChrSpecializationEntry
{
    std::int8_t ClassID;
    std::int8_t OrderIndex;
    bool IsPetSpecialization() const { return ClassID == 0; }
};
struct Store
{
    std::unordered_map<uint32, ChrSpecializationEntry> entries;
    ChrSpecializationEntry const* LookupEntry(uint32 id) const
    {
        auto it = entries.find(id);
        return it == entries.end() ? nullptr : &it->second;
    }
} sChrSpecializationStore;
struct PlayerCharacterSetup { static uint32 FindPlayerTalentType(Player* player); };
'''
    harness += '\n#define MAX_SPECIALIZATIONS ' + maximum[1] + '\n' + match[0]
    harness += r'''
void expect(Player* player, uint32 expected, char const* description)
{
    if (PlayerCharacterSetup::FindPlayerTalentType(player) != expected)
        throw std::runtime_error(description);
}
int main()
{
    // Use fixture IDs unrelated to their order, so returning a DB2 ID fails.
    for (std::int8_t order = 0; order < 4; ++order)
    {
        uint32 id = 8000 + order;
        sChrSpecializationStore.entries[id] = {11, order};
        Player druid{id, 11};
        expect(&druid, order, "all four druid orders must be reportable");
    }
    sChrSpecializationStore.entries[9100] = {12, 1};
    Player demonHunter{9100, 12};
    expect(&demonHunter, 1, "demon hunter second specialization");
    Player changing{8001, 11};
    expect(&changing, 1, "initial active specialization");
    changing.specId = 8002;
    expect(&changing, 2, "read current specialization without a stale cache");
    Player wrongClass{8001, 8};
    expect(&wrongClass, 255, "reject specialization belonging to another class");
    Player missing{99999, 11};
    expect(&missing, 255, "missing DB2 row must not report the first specialization");
    Player noSelection{0, 11};
    expect(&noSelection, 255, "no selected specialization");
    expect(nullptr, 255, "null player");
    sChrSpecializationStore.entries[9200] = {0, 0};
    Player pet{9200, 0};
    expect(&pet, 255, "pet specialization is not a character specialization");
    sChrSpecializationStore.entries[9300] = {11, -1};
    Player negative{9300, 11};
    expect(&negative, 255, "negative DB2 order");
    sChrSpecializationStore.entries[9400] = {11, 4};
    Player tooLarge{9400, 11};
    expect(&tooLarge, 255, "out-of-range DB2 order");
    std::cout << "PASS: active specialization reporting and invalid-data cases\n";
}
'''
    with tempfile.TemporaryDirectory(prefix='1kycore-specialization-') as directory:
        source_path = Path(directory) / 'reporting.cpp'
        executable = Path(directory) / ('reporting.exe' if os.name == 'nt' else 'reporting')
        source_path.write_text(harness, encoding='utf-8')
        subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-Wall', '-Wextra', '-Werror', str(source_path), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == '__main__':
    main()
