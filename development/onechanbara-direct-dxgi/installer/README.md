# Onechanbara v1.7 direct DXGI integrated installer

Revision: `shared-image-copy-1`. Follow-up to the captured freeze and low-FPS result of the first direct-backbuffer candidate. This revision renders to one shared image, waits for the previous D3D12 copy before reuse, and copies to DXGI backbuffers. No NVIDIA profiles are created or changed.

Full Windows build: https://github.com/slimshadykor-cmd/korean-patches/actions/runs/42471903537

Package SHA-256: `3cb398331c6716d4a6d69c9e4b26e4d2674ffeeeb99f4fa4878740740e500ed5`

33 synchronization checks execute production methods with mocked Windows/GPU objects. Four logging checks exercise the production slow-stage timer with a mocked logger. Fourteen installation/filesystem checks include upgrading an existing direct runtime to a different executable hash, rollback, and preservation of original EXE/config/save data. The shipping assembly resource/hash/version/ISO-rejection/manifest checks passed. Full Windows native emulator build passed.

No actual Windows GPU gameplay test has been performed. The captured freeze root cause has not been established, and this revision is a candidate pending the user's GPU test. See `regression_192245/revision-notes.txt`.

The build script records the original workspace layout: direct_v17 alongside integrated_v17 (localization payload and NET48 references) and non_nv/integration (NativeLauncher.cs). The native runtime and its provenance are in the adjacent runtime directory of this branch. The unchanged icon and localization payload are included in the integrated distribution and are not duplicated in this source snapshot. Rebuild refreshes both embedded executable hashes, including when replacing previously substituted values.
