# Onechanbara v1.3.0 release checkpoint

This checkpoint reconstructs the verified Windows patcher from the unchanged official v1.2.9 release. The public ZIP contains only the EXE and two user instructions.

`build_release.py` verifies the baseline, recipe, executable, embedded package and final ZIP hashes. The workflow validates the shipping EXE on Windows .NET Framework before publishing. It then adds navigation to seven previous Onechanbara releases. The main category README is updated separately after successful publication.

The 107 text records are documented in `audit/translations.json`; identifiers and placeholder tokens are preserved. Only default.xex differs from v1.2.9. Images and the title-screen v1.2.9 label remain unchanged by request; the new patcher identifies itself as v1.3.0.

`source/` contains the local production and validation scripts. Rebuilding the binary from game data requires the preceding audit1024 workspace (original/current game assets, Unicode extraction results, glyph mapping, and XEX codec), plus .NET SDK 8.0.100, .NET Framework 4.8 reference assemblies, numpy, cryptography and Unicorn 2.1.4. The checkpoint does not include game ISOs. End users do not need these dependencies.

`audit/iso_validation.json` records the actual managed core tests with real nonvideo assets in synthetic XDVDFS images. It explicitly records empty directory remnants observed under the Linux harness; payload files and partial ISO outputs were removed. Windows cleanup is independently gated in the release workflow. No Xenia all-chapter gameplay or GUI rendering is claimed.
