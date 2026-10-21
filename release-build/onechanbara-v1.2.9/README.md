# Onechanbara Korean v1.2.9 release reconstruction

`build_release.py` reconstructs the exact verified Windows patcher from the
official 2026-10-19 v1.2.8 ZIP and the versioned copy/literal recipe. It verifies
the baseline, executable, embedded manifest, and final distribution ZIP hashes.
Only the EXE, Korean instructions, and original ISO hash instructions enter the
public distribution. Source files and audit tools remain in this build branch.

```sh
python3 release-build/onechanbara-v1.2.9/build_release.py --out release-dist
```

The only game assets changed from the latest v1.2.8 are `default.xex` and
`Media/Menu/title2d.cat`. The executable is byte-identical to the Korean
Loading Test01 build that the user tested in Xenia. The other 156 manifest
paths and their payloads are unchanged. The established ISO application core
is unchanged; updates create a separate output ISO.

The source snapshot records the local build/audit scripts. Their complete
asset-level rebuild requires the user's original Media, Demo, Mission and
Story files, original default.xex, v1.2.5/v1.2.8 releases, and the earlier
translation source checkpoints. Those game source assets are not included
in this branch. The independently executable release reconstruction above
uses only the public v1.2.8 baseline and this branch.

Audit dependencies: Python 3.12, Pillow, NumPy, cryptography,
PyCryptodome 3.23.0, Unicorn 2.1.4, Capstone 5.0.7. Windows executable build:
.NET SDK 8.0.100 C# compiler with .NET Framework 4.8 reference assemblies
(Microsoft.NETFramework.ReferenceAssemblies.net48 1.0.3). The game code tests
use actual PowerPC instructions with OS APIs or object-name getters mocked
where stated in each report. They are not an end-to-end Xenia playthrough.

The user reported approximately 60 seconds becoming 30–35 seconds in a
previously slow loading segment. This is a user-observed approximate result,
not a controlled benchmark or a guarantee for other machines.
