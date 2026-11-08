Onechanbara v1.7 diagnostic Vulkan GPU interval probe

Integration
- Import transform.py and call apply(files) after creating the paced-output-1
  source dictionary. It modifies VulkanPresenter only and adds one helper header.
- cvars::onechanbara_diagnostics must be declared in vulkan_presenter.cc.
- The probe supports both native Vulkan and direct DXGI presenter paths.

What the number means
- TOP_OF_PIPE -> BOTTOM_OF_PIPE timestamps surround the final presentation pass.
- This GPU interval can include semaphore stalls and other queue overlap. It is
  not engine-busy time or the time spent rendering the guest Xbox 360 scene.
- This is not the physical monitor display time and not a D3D12 copy measurement.
- A 64-bit result and timestampValidBits mask handle a single counter wrap.
  More than one complete counter period cannot be unwrapped from two samples.
  Timestamp bit width and period are logged so that ambiguity remains visible.

Lifetime / progress
- Disabled diagnostics do not create or record queries.
- Eight query pairs form a bounded ring. Unready slots are skipped, never waited.
- Readback happens only for earlier submitted samples whose existing Xenia
  completion index has completed. This avoids accepting stale availability from
  a previous use of a query while the new reset is still waiting on the GPU.
- Query reads request 64-bit values plus availability without WAIT/PARTIAL flags.
- An early return or failed queue submission does not mark its query pair pending.
- Destruction follows the existing swapchain-retirement completion wait and adds
  no wait, queue submission, or resource barrier of its own.
- Aggregate output is at most once per second, plus a final retirement summary.
- Unsupported timestamp APIs, allocation failure, or full ring only disable or
  skip diagnostic samples. They do not terminate or stall game rendering.

Validation
Run: python3 diagnostic_v17/gpu_metrics/test_transform.py
The C++ helper is compiled against the actual Vulkan-Headers 1.3.296 headers.
Mock API cases cover disabled/unsupported/allocation-failed probes, the completed
submission gate, query availability, ring pressure, failed/unsubmitted samples,
query-error handling, cleanup, and timestamp wrap. The exact paced patch is
applied to source fixtures and transformed without adding wait/submit calls.
Physical Windows GPU behavior remains untested locally.

Primary references checked
https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdWriteTimestamp.html
https://docs.vulkan.org/refpages/latest/refpages/source/vkGetQueryPoolResults.html
