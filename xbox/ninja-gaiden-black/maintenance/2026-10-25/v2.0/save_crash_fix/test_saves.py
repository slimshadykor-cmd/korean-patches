"""Audit cross-mode serialization using the newly captured Black gameplay progress.

This is NOT a replay of the newly reported BLACK save-menu crash. Only the
progress bytes come from the new RAM dump; OS/file I/O, heap, and signing remain
modeled as in test_native.Machine. Native serializer/compressor/readers run.
"""
import sys, json, hashlib, struct, itertools
from pathlib import Path
sys.path.insert(0, '.')
sys.path.insert(0, 'save_fix9')
from test_native import *
from crash_analysis.ram import Ram

capture = Ram('upload/ngb_save_crash.bin').read(BASE, SIZE)

class CapturedMachine(Machine):
    def write_capture(self, mode, path, seq):
        self.path = path
        u = self.u
        u.mem_write(BASE, capture)
        setstate(u, (mode, seq % 2, (seq // 2) % 2))
        seed = bytes(u.mem_read(BASE, SIZE))
        ctx, ui, vt = 0xc08dc0, 0x1709000, 0x170b000
        for slot in range(30):
            put(u, ctx + slot * 0x208 + 0x208, 0xffffffff)
        if path == 'overwrite':
            put(u, ctx + 0x208, 0)
        put(u, ui + 0x18, 1)
        put(u, ui + 0x1c, vt)
        put(u, vt + 8, 0x3001000)
        self.invoke(0x1876f0, [], ecx=ui)
        assert get(u, D['status']) == 0
        self.guards()
        saved = bytes(u.mem_read(BASE, SIZE))
        assert saved[:-12] == seed[:-12]
        return saved, state(u)

rows = []
for heap, lifecycle, reader, modes in itertools.product(
    ['aligned', 'null'], ['warm', 'fresh_cpu'],
    ['direct', 'generic', 'alternate'],
    [(0, 0), (1, 1), (0, 1), (1, 0), (0, 1, 0), (1, 0, 1)]):
    m = CapturedMachine(heap=heap)
    for seq, mode in enumerate(modes):
        saved, st = m.write_capture(mode, 'new' if seq == 0 else 'overwrite', seq)
        if lifecycle == 'fresh_cpu':
            m = CapturedMachine(m.disk.copy(), heap)
        setstate(m.u, tuple(1-x for x in st))
        m.u.mem_write(BASE, bytes(SIZE))
        assert m.read(reader) == 0
        assert bytes(m.u.mem_read(BASE, SIZE)) == saved
        assert state(m.u) == st
    rows.append({'heap':heap, 'lifecycle':lifecycle, 'reader':reader,
                 'modes':list(modes), 'operations':len(modes),
                 'serialized_length':len(m.disk['data']), 'pass':True})
    print('PASS', heap, lifecycle, reader, modes, flush=True)

report = {'sha256':hashlib.sha256(b).hexdigest(), 'scope':__doc__,
          'capture_bytes':len(capture), 'capture_sha256':hashlib.sha256(capture).hexdigest(),
          'nonzero_capture_bytes':sum(x != 0 for x in capture),
          'cases':rows, 'case_count':len(rows),
          'write_read_pairs':sum(r['operations'] for r in rows)}
Path('save_crash_fix/save_regression.json').write_text(json.dumps(report, indent=2))
print('PASS', report['case_count'], 'cases', report['write_read_pairs'], 'write/read pairs')
