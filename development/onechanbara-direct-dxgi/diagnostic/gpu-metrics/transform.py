"""Attach asynchronous final-output timestamps to the paced integration.

Call apply(files) after generating the normal paced files and adding the
onechanbara_diagnostics cvar declaration. No original emulator files are edited.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = 'src/xenia/ui/vulkan/'


def apply(files):
    def replace(name, old, new):
        content = files[name]
        assert content.count(old) == 1, (name, old[:120], content.count(old))
        files[name] = content.replace(old, new)

    h = PREFIX + 'vulkan_presenter.h'
    cc = PREFIX + 'vulkan_presenter.cc'
    helper = PREFIX + 'onechanbara_display/ocb_gpu_timing.h'
    files[helper] = (ROOT / 'ocb_gpu_timing.h').read_text()
    replace(h, '#include "xenia/ui/vulkan/vulkan_gpu_completion_timeline.h"',
        '#include "xenia/ui/vulkan/vulkan_gpu_completion_timeline.h"\n'
        '#include "xenia/ui/vulkan/onechanbara_display/ocb_gpu_timing.h"')
    replace(h, '    VulkanGPUCompletionTimeline completion_timeline;',
        '    VulkanGPUCompletionTimeline completion_timeline;\n'
        '    OcbVulkanOutputGpuTiming gpu_output_timing;')
    replace(cc, '    completion_timeline.AwaitAllSubmissions();\n'
                '    // Also wait for the presentation queue',
        '    completion_timeline.AwaitAllSubmissions();\n'
        '    gpu_output_timing.DestroyAfterIdle();\n'
        '    // Also wait for the presentation queue')
    replace(cc, '  // Non-zero extents needed for both the viewport (width must not be zero) and',
        '''  // Optional timestamps cover the final presentation GPU interval,
  // possibly including semaphore stalls. They are not engine-busy time.
  // The existing completion update suffices; the probe never adds a wait.
  const auto& gpu_timing_ifn = vulkan_device_->vulkan_instance()->functions();
  const OcbVulkanOutputGpuTiming::Context gpu_timing_context{
      device, vulkan_device_->physical_device(),
      vulkan_device_->queue_family_graphics_compute(),
      gpu_timing_ifn.vkGetDeviceProcAddr,
      gpu_timing_ifn.vkGetPhysicalDeviceProperties,
      gpu_timing_ifn.vkGetPhysicalDeviceQueueFamilyProperties};
  const int gpu_timing_slot = paint_context_.gpu_output_timing.Begin(
      cvars::onechanbara_diagnostics, gpu_timing_context, draw_command_buffer,
      current_paint_submission_index,
      paint_context_.completion_timeline.GetCompletedSubmissionFromLastUpdate());

  // Non-zero extents needed for both the viewport (width must not be zero) and''')
    replace(cc, '  if (dfn.vkEndCommandBuffer(draw_command_buffer) != VK_SUCCESS) {',
        '  paint_context_.gpu_output_timing.End(gpu_timing_slot, draw_command_buffer);\n'
        '  if (dfn.vkEndCommandBuffer(draw_command_buffer) != VK_SUCCESS) {')
    replace(cc, '  if (execute_ui_drawers) {\n'
                '    // Also update the completion timeline',
        '  paint_context_.gpu_output_timing.Submitted(gpu_timing_slot);\n'
        '  if (execute_ui_drawers) {\n'
        '    // Also update the completion timeline')
    return files
