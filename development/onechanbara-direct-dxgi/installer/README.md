# Onechanbara v1.7 application-owned DXGI output candidate

The previous `shared-image-copy-1` build was verified as active in the supplied
log, but gameplay video still fell to 23–37 FPS. Its 100 ms CPU diagnostic
threshold recorded no slow stages. The GPU-performance cause remains unconfirmed.

`paced-output-1` changes the opt-in display path in two places: normal gameplay
uses immediate guest-output-thread presentation, and acquire retains the current
frame across ordinary waits beyond 16 ms, up to a 250 ms bound. Active emulator
dialogs and explicit UI-thread settings retain UI presentation and its 16 ms wait.
The standard Vulkan and D3D12 scheduling policy is unchanged. DXGI continues to
use VSync (`Present(1, 0)`) and shared-image copying.

Once-per-second CPU-stage aggregates distinguish successful Present calls from
attempts. These are not GPU execution timings or physical display FPS. The
launcher exit receipt also records the runtime SHA-256.

Validation includes extracted scheduling tests (7), actual bridge/vendor methods
against mocked Windows/GPU APIs (43), and deterministic metrics tests (9). Native
Windows compilation and installer-resource checks are recorded separately.
**No native GPU gameplay validation has passed for this revision.**

Only `src/xenia/ui/` is modified by the complete source patch. The Korean payload,
guest timing/animation code, resolution scale, game clock, shared save path,
original emulator and common settings are preserved. The launcher and runtime
contain no NVIDIA driver-profile writes. Version 1.7 remains the user-visible
version; `paced-output-1` identifies this display revision in the log.

The full installer can update an existing v1.7 ISO shortcut without rebuilding
the ISO. Installation is transactional and verifies the replacement runtime hash.

Source build:
https://github.com/slimshadykor-cmd/korean-patches/actions/runs/42477979611

Pinned upstream:
https://github.com/xenia-canary/xenia-canary/tree/b083312b8b18e07e6e410b82104191f126722794

Runtime licenses remain in the runtime archive. `reproduction/` contains patch
generation inputs; the complete authoritative patch is in `../source/`.
