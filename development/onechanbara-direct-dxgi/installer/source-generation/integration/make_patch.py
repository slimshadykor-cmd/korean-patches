from pathlib import Path
import difflib, hashlib, json, shutil, subprocess

root=Path(__file__).resolve().parent.parent
base=root/'dependencies/xenia-canary-b083312b8'
out=root/'xenia_work'
bridge=root/'bridge'
subprocess.run(['python3',str(bridge/'prepare_vendor.py')],check=True)
subprocess.run(['python3',str(bridge/'prepare_xenia_device.py')],check=True)
files={}
def load(name):
    if name not in files: files[name]=(base/name).read_text()
    return files[name]
def replace(name,old,new):
    s=load(name)
    assert s.count(old)==1,(name,old[:100],s.count(old))
    files[name]=s.replace(old,new)
vp='src/xenia/ui/vulkan/'
# The opt-in bridge may apply backpressure on the guest output thread.
# Default Vulkan and D3D12 presentation keep the original scheduling policy.
replace('src/xenia/ui/presenter.h',
        '  virtual void DisconnectPaintingFromSurfaceFromUIThreadImpl() = 0;',
        '''  virtual void DisconnectPaintingFromSurfaceFromUIThreadImpl() = 0;
  virtual bool PreferGuestOutputThreadWithImplicitVsync() const { return false; }''')
replace('src/xenia/ui/presenter.cc',
        '  if (surface_paint_connection_has_implicit_vsync_) {',
        '''  if (surface_paint_connection_has_implicit_vsync_ &&
      !PreferGuestOutputThreadWithImplicitVsync()) {''')
for f in ['vulkan_device.cc','vulkan_device.h']:
    files[vp+f]=(bridge/'xenia_device_preparation'/f).read_text()
provider=vp+'vulkan_provider.cc'
replace(provider,'namespace xe {','''DEFINE_bool(vulkan_direct_dxgi, false,
            "Use application-owned DXGI output with Vulkan rendering on Windows.",
            "Vulkan");

namespace xe {''')
s=load(provider)
assert s.count('with_presentation);')==2
files[provider]=s.replace('with_presentation);','with_presentation, with_presentation && cvars::vulkan_direct_dxgi);')
h=vp+'vulkan_presenter.h'
replace(h, '#include <memory>', '#include <memory>\n#include <thread>')
replace(h, '  void DisconnectPaintingFromSurfaceFromUIThreadImpl() override;',
        '''  void DisconnectPaintingFromSurfaceFromUIThreadImpl() override;
  bool PreferGuestOutputThreadWithImplicitVsync() const override {
    return paint_context_.direct_dxgi != nullptr;
  }''')
replace(h,'    VkSurfaceKHR vulkan_surface = VK_NULL_HANDLE;','''    // Windows bridge owns imported images and DXGI swapchain. No DRS profile.
    void* direct_dxgi = nullptr;
    std::thread::id direct_dxgi_ui_thread;
    VkSurfaceKHR vulkan_surface = VK_NULL_HANDLE;''')
cc=vp+'vulkan_presenter.cc'
replace(cc,'#include "xenia/ui/vulkan/vulkan_presenter.h"','''#include "xenia/ui/vulkan/vulkan_presenter.h"
#if XE_PLATFORM_WIN32
#include "xenia/ui/vulkan/onechanbara_display/vulkan_dxgi_bridge.h"
#endif''')
replace(cc,'  VkFormat new_swapchain_format;','''  VkFormat new_swapchain_format;

#if XE_PLATFORM_WIN32
  if (vulkan_device_->dxgi_display_enabled()) {
    paint_context_.DestroySwapchainAndVulkanSurface();
    if (new_surface.GetType() != Surface::kTypeIndex_Win32Hwnd ||
        !new_surface_width || !new_surface_height) {
      return SurfacePaintConnectResult::kFailureSurfaceUnusable;
    }
    const auto& window_surface = static_cast<const Win32HwndSurface&>(new_surface);
    const char* sharing_extensions[] = {
        VK_KHR_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME,
        VK_KHR_EXTERNAL_SEMAPHORE_WIN32_EXTENSION_NAME};
    OcbDisplayConfig config{};
    config.instance = instance;
    config.physical_device = vulkan_device_->physical_device();
    config.device = device;
    config.queue_family = vulkan_device_->queue_family_graphics_compute();
    config.queue = vulkan_device_->queue_families()[config.queue_family].queues[0]->queue;
    config.get_instance_proc = ifn.vkGetInstanceProcAddr;
    config.get_device_proc = ifn.vkGetDeviceProcAddr;
    config.window = window_surface.hwnd();
    config.width = new_surface_width; config.height = new_surface_height;
    config.timeline_enabled = VK_TRUE;
    config.enabled_extension_count = 2;
    config.enabled_extensions = sharing_extensions;
    char error[256]{};
    paint_context_.direct_dxgi = OcbDisplayCreate(&config, error, sizeof(error));
    if (!paint_context_.direct_dxgi) {
      XELOGE("Vulkan direct DXGI initialization failed: {}", error);
      return SurfacePaintConnectResult::kFailure;
    }
    paint_context_.swapchain_extent = {new_surface_width, new_surface_height};
    paint_context_.direct_dxgi_ui_thread = std::this_thread::get_id();
    paint_context_.present_queue_family = config.queue_family;
    // VSync remains enabled. The bridge-specific scheduling override keeps
    // normal gameplay presentation on the guest output thread, so a ready
    // frame isn't replaced while waiting for a UI-thread paint notification.
    paint_context_.swapchain_is_fifo = true;
    new_swapchain_format = VK_FORMAT_R8G8B8A8_UNORM;
    XELOGI("Onechanbara direct DXGI output: {}x{}, shared image ring, buffered-output-1, no driver profile",
           new_surface_width, new_surface_height);
  } else
#endif
  {''')
replace(cc,'  // From now on, in case of failure,','''  }  // Native Vulkan swapchain path.

  // From now on, in case of failure,''')
replace(cc,'    render_pass_attachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;\n    render_pass_attachment.finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;','''    render_pass_attachment.initialLayout = paint_context_.direct_dxgi
        ? VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL : VK_IMAGE_LAYOUT_UNDEFINED;
    render_pass_attachment.finalLayout = paint_context_.direct_dxgi
        ? VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL : VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;''')
replace(cc,'  // Get the swapchain images.','''#if XE_PLATFORM_WIN32
  if (paint_context_.direct_dxgi) {
    paint_context_.swapchain_images.resize(3);
    if (OcbDisplayGetImages(paint_context_.direct_dxgi,
          paint_context_.swapchain_images.data(), 3) != OCB_OK) {
      paint_context_.DestroySwapchainAndVulkanSurface();
      return SurfacePaintConnectResult::kFailure;
    }
  } else
#endif
  {
  // Get the swapchain images.''')
replace(cc,'  // Create the image views and the framebuffers.','''  }

  // Create the image views and the framebuffers.''')
replace(cc,'  // Create per-swapchain-image present semaphores to avoid','''  if (!paint_context_.direct_dxgi) {
  // Create per-swapchain-image present semaphores to avoid''')
replace(cc,'  is_vsync_implicit_out = paint_context_.swapchain_is_fifo;','''  }
  is_vsync_implicit_out = paint_context_.swapchain_is_fifo;''')
replace(cc,'  if (swapchain != VK_NULL_HANDLE) {\n    completion_timeline.AwaitAllSubmissions();','''  if (swapchain != VK_NULL_HANDLE || direct_dxgi) {
    completion_timeline.AwaitAllSubmissions();''')
replace(cc,'  present_queue_family = UINT32_MAX;\n  if (vulkan_surface != VK_NULL_HANDLE) {','''#if XE_PLATFORM_WIN32
  if (direct_dxgi) {
    OcbDisplayDestroy(direct_dxgi);
    direct_dxgi = nullptr;
  }
#endif
  present_queue_family = UINT32_MAX;
  if (vulkan_surface != VK_NULL_HANDLE) {''')
replace(cc,'  if (cvars::vulkan_semaphore_reuse_workaround) {','''  if (!paint_context_.direct_dxgi && cvars::vulkan_semaphore_reuse_workaround) {''')
replace(cc,'  uint32_t swapchain_image_index;\n  VkResult acquire_result = dfn.vkAcquireNextImageKHR(','''  uint32_t swapchain_image_index;
#if XE_PLATFORM_WIN32
  OcbDisplayFrame dxgi_frame{};
  if (paint_context_.direct_dxgi) {
    // Retain the current gameplay frame across normal 16.7 / 33.3 / 50 ms
    // presentation waits. UI paints retain the short responsiveness bound.
    const bool ui_paint = std::this_thread::get_id() ==
        paint_context_.direct_dxgi_ui_thread;
    const int result = OcbDisplayAcquire(paint_context_.direct_dxgi, &dxgi_frame,
                                         ui_paint ? 16 : 250);
    if (result == OCB_NOT_READY) return PaintResult::kNotPresented;
    if (result != OCB_OK) {
      XELOGE("Direct DXGI acquire: {}", OcbDisplayLastError(paint_context_.direct_dxgi));
      return PaintResult::kNotPresentedConnectionOutdated;
    }
    swapchain_image_index = dxgi_frame.image_index;
    dfn.vkCmdPipelineBarrier(draw_command_buffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
        VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, 0, 0, nullptr, 0, nullptr,
        1, &dxgi_frame.acquire_barrier);
  } else
#endif
  {
  VkResult acquire_result = dfn.vkAcquireNextImageKHR(''')
replace(cc,'  // Non-zero extents needed for both the viewport (width must not be zero) and','''  }

  // Non-zero extents needed for both the viewport (width must not be zero) and''')
replace(cc,'  dfn.vkCmdEndRenderPass(draw_command_buffer);\n\n  dfn.vkEndCommandBuffer(draw_command_buffer);','''  dfn.vkCmdEndRenderPass(draw_command_buffer);
#if XE_PLATFORM_WIN32
  if (paint_context_.direct_dxgi) {
    dfn.vkCmdPipelineBarrier(draw_command_buffer, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, 0, 0, nullptr, 0, nullptr,
        1, &dxgi_frame.release_barrier);
  }
#endif
  if (dfn.vkEndCommandBuffer(draw_command_buffer) != VK_SUCCESS) {
#if XE_PLATFORM_WIN32
    if (paint_context_.direct_dxgi) OcbDisplayCancel(paint_context_.direct_dxgi);
#endif
    return PaintResult::kNotPresentedConnectionOutdated;
  }''')
replace(cc,'  VkSemaphore present_semaphore =\n      paint_context_.swapchain_image_present_semaphores[swapchain_image_index];','''  VkSemaphore present_semaphore = VK_NULL_HANDLE;
  VkTimelineSemaphoreSubmitInfo dxgi_timeline{VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO};
  uint64_t dxgi_wait_value = 0, dxgi_signal_value = 0;
#if XE_PLATFORM_WIN32
  if (paint_context_.direct_dxgi) {
    if (OcbDisplayGetSync(paint_context_.direct_dxgi, &dxgi_frame, &acquire_semaphore,
                         &present_semaphore, &dxgi_wait_value, &dxgi_signal_value) != OCB_OK) {
      OcbDisplayCancel(paint_context_.direct_dxgi);
      return PaintResult::kNotPresentedConnectionOutdated;
    }
    dxgi_timeline.waitSemaphoreValueCount = 1;
    dxgi_timeline.pWaitSemaphoreValues = &dxgi_wait_value;
    dxgi_timeline.signalSemaphoreValueCount = 1;
    dxgi_timeline.pSignalSemaphoreValues = &dxgi_signal_value;
  } else
#endif
  {
    present_semaphore = paint_context_.swapchain_image_present_semaphores[swapchain_image_index];
  }''')
# This exact submit-info block is unique to PaintAndPresentImpl.
replace(cc,'  submit_info.pNext = nullptr;\n  submit_info.waitSemaphoreCount = 1;',
'''  submit_info.pNext = paint_context_.direct_dxgi ? &dxgi_timeline : nullptr;
  submit_info.waitSemaphoreCount = 1;''')
replace(cc,'\n    // The image is in an acquired state - but now, it will be in it forever.','''
#if XE_PLATFORM_WIN32
    if (paint_context_.direct_dxgi) OcbDisplayCancel(paint_context_.direct_dxgi);
#endif
    // The image is in an acquired state - but now, it will be in it forever.''')
replace(cc,'  VkPresentInfoKHR present_info;','''#if XE_PLATFORM_WIN32
  if (paint_context_.direct_dxgi) {
    // VulkanGPUCompletionTimeline released the Vulkan queue lock above.
    if (OcbDisplayPresentSubmitted(paint_context_.direct_dxgi, &dxgi_frame) == OCB_OK) {
      display_timer.Presented();
      return PaintResult::kPresented;
    }
    XELOGE("Direct DXGI present: {}", OcbDisplayLastError(paint_context_.direct_dxgi));
    return PaintResult::kNotPresentedConnectionOutdated;
  }
#endif

  VkPresentInfoKHR present_info;''')
# Time only the modified display path. Slow calls go to the existing Xenia log.
replace(cc,'#include <cstdint>', '#include <cstdint>\n#include <chrono>')
replace(cc,'namespace xe {',
        (root/'integration/display_metrics.inc').read_text()+'\nnamespace xe {')
replace(cc,'''  // Begin the submission in place of the one not currently potentially used on''','''  OcbDisplayStageTimer display_timer(paint_context_.direct_dxgi != nullptr,
      std::this_thread::get_id() == paint_context_.direct_dxgi_ui_thread);
  // Begin the submission in place of the one not currently potentially used on''')
replace(cc,'''  const PaintContext::Submission& paint_submission =''','''  display_timer.Stage("command buffer preparation");
  const PaintContext::Submission& paint_submission =''')
replace(cc,'''    const int result = OcbDisplayAcquire(''','''    display_timer.Stage("DXGI acquire");
    const int result = OcbDisplayAcquire(''')
replace(cc,'''    swapchain_image_index = dxgi_frame.image_index;''','''    display_timer.Stage("Vulkan image drawing");
    swapchain_image_index = dxgi_frame.image_index;''')
replace(cc,'''  const VkResult submit_result =
      paint_context_.completion_timeline.AcquireFenceAndSubmit(''','''  display_timer.Stage("Vulkan queue submit");
  const VkResult submit_result =
      paint_context_.completion_timeline.AcquireFenceAndSubmit(''')
replace(cc,'''    // VulkanGPUCompletionTimeline released the Vulkan queue lock above.''','''    display_timer.Stage("DXGI copy and present");
    // VulkanGPUCompletionTimeline released the Vulkan queue lock above.''')
cm=vp+'CMakeLists.txt'
replace(cm,'xe_target_defaults(xenia-ui-vulkan)','''xe_target_defaults(xenia-ui-vulkan)
if(WIN32)
  target_sources(xenia-ui-vulkan PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/onechanbara_display/vulkan_dxgi_bridge.cc)
  target_compile_definitions(xenia-ui-vulkan PRIVATE OCB_DISPLAY_STATIC)
endif()''')
for name in ['vulkan_dxgi_bridge.cc','vulkan_dxgi_bridge.h','frame_contract.h',
             'vendor/vk_dxgi.h','vendor/LICENSE','vendor/local-changes.patch']:
    files[vp+'onechanbara_display/'+name]=(bridge/name).read_text()
patch=''
for name,content in sorted(files.items()):
    original=(base/name).read_text() if (base/name).exists() else ''
    for line in difflib.unified_diff(original.splitlines(True),content.splitlines(True),
        fromfile=('a/'+name if original else '/dev/null'),tofile='b/'+name):
        patch += line if line.endswith('\n') else line+'\n\\ No newline at end of file\n'
    target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content)
(root/'integration/xenia-direct-dxgi.patch').write_text(patch)
(root/'integration/source-manifest.json').write_text(json.dumps({
    'base_commit':'b083312b8b18e07e6e410b82104191f126722794',
    'files':{n:hashlib.sha256(t.encode()).hexdigest() for n,t in files.items()}},indent=2))
print('Generated complete device/provider/presenter/build integration patch:',len(files),'files',len(patch),'bytes')
