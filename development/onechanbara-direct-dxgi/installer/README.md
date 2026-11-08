# Onechanbara v1.7 direct DXGI integrated installer

Shipping source snapshot. Full Xenia build: https://github.com/slimshadykor-cmd/korean-patches/actions/runs/42468237049

Package SHA-256: `109a1393e8e462bb3125c82bf24134ba9206573d774c3ca7fe3e0f5adc0df4bb`

The installer embeds the unchanged v1.7 localization payload, the native Xenia build and an asInvoker native launcher. It creates no NVIDIA profiles. The shared emulator/config and original content location are preserved.

12 installation and rollback checks passed with a real filesystem and mocked shortcut COM/original emulator identity. Resource/hash/version/rejection checks passed on the shipping managed assembly. No native Windows GPU gameplay test was possible. See the validation JSON files.

The build script records the original workspace layout: direct_v17 alongside integrated_v17 (payload, NET48 references) and non_nv/integration (NativeLauncher.cs). The runtime is in the adjacent runtime directory of this branch. Source hashes in Manage-Onechanbara.ps1 are the final shipping hashes; fixture tests originally ran before hash substitution. Original icon and localization payload are available in the integrated distribution, not duplicated here.
