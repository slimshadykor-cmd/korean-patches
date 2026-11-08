from pathlib import Path

HERE=Path(__file__).resolve().parent

def apply(files):
    def rep(path,old,new):
        s=files[path]
        assert s.count(old)==1,(path,old[:100],s.count(old))
        files[path]=s.replace(old,new)
    vp='src/xenia/ui/vulkan/'
    cc=vp+'vulkan_presenter.cc'; h=vp+'vulkan_presenter.h'
    pc='src/xenia/ui/presenter.cc'; ph='src/xenia/ui/presenter.h'
    bh=vp+'onechanbara_display/vulkan_dxgi_bridge.h'
    bc=vp+'onechanbara_display/vulkan_dxgi_bridge.cc'
    vendor=vp+'onechanbara_display/vendor/vk_dxgi.h'
    files['src/xenia/ui/onechanbara_diagnostic_statistics.h']=(HERE/'diagnostic_statistics.h').read_text()
    rep(vp+'vulkan_provider.cc','DEFINE_bool(vulkan_direct_dxgi, false,', '''DEFINE_bool(onechanbara_guest_output, true,
            "Diagnostic scheduling choice; retain the original UI safety checks.",
            "Vulkan");
DEFINE_bool(vulkan_direct_dxgi, false,''')
    rep(pc,'#include "xenia/ui/presenter.h"','#include "xenia/ui/presenter.h"\n#include <chrono>')
    rep(pc,'namespace xe {','''DEFINE_bool(onechanbara_diagnostics, false,
            "Collect CPU/API frame-delivery diagnostics for Onechanbara.", "Display");

namespace xe {''')
    rep(ph,'    bool is_8bpc;','''    bool is_8bpc;
    uint64_t diagnostic_id = 0;
    int64_t diagnostic_publish_ns = 0;''')
    rep(ph,'  virtual bool PreferGuestOutputThreadWithImplicitVsync() const { return false; }','''  virtual bool PreferGuestOutputThreadWithImplicitVsync() const { return false; }
  uint64_t DiagnosticProduced() const {
    return diagnostic_produced_.load(std::memory_order_relaxed);
  }
  std::atomic<uint64_t> diagnostic_produced_{0};''')
    rep(pc,'  // Make the new image the next to present on the host (the "ready" one),','''  if (cvars::onechanbara_diagnostics) {
    // Metadata travels under the existing mailbox release/acquire protocol.
    // No extra image handoff, lock or synchronization is introduced.
    writable_properties.diagnostic_id =
        diagnostic_produced_.fetch_add(1, std::memory_order_relaxed) + 1;
    writable_properties.diagnostic_publish_ns =
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count();
  }

  // Make the new image the next to present on the host (the "ready" one),''')
    rep(h,'#include <thread>','#include <thread>\n#include "xenia/ui/onechanbara_diagnostic_statistics.h"')
    rep(h,'''  bool PreferGuestOutputThreadWithImplicitVsync() const override {
    return paint_context_.direct_dxgi != nullptr;
  }''','''  bool PreferGuestOutputThreadWithImplicitVsync() const override;
  OcbDisplayStatistics diagnostic_cpu_{};
  uint64_t diagnostic_generation_ = 0;''')
    old=(HERE/'display_metrics.inc').read_text()
    rep(cc,old,(HERE/'diagnostic_metrics.inc').read_text())
    rep(cc,'namespace {\nclass OcbDisplayStageTimer', '''DECLARE_bool(onechanbara_diagnostics);
DECLARE_bool(onechanbara_guest_output);

namespace {
class OcbDisplayStageTimer''')
    rep(cc,'  VkFormat new_swapchain_format;','''  VkFormat new_swapchain_format;
  paint_context_.direct_dxgi_ui_thread = std::this_thread::get_id();''')
    rep(cc,'    config.timeline_enabled = VK_TRUE;','''    config.timeline_enabled = VK_TRUE;
    config.diagnostics = cvars::onechanbara_diagnostics;''')
    rep(cc,'shared image copy, paced-output-1, no driver profile','shared image copy, diagnostic-output-1, no driver profile')
    rep(cc,'  is_vsync_implicit_out = paint_context_.swapchain_is_fifo;','''  is_vsync_implicit_out = paint_context_.swapchain_is_fifo;
  if (cvars::onechanbara_diagnostics) {
    diagnostic_cpu_ = {};
    diagnostic_cpu_.generation = ++diagnostic_generation_;
    XELOGI("Onechanbara diagnostic connection: revision=diagnostic-output-1 generation={} path={} "
           "guest_preference={} implicit_vsync={} width={} height={} dxgi_ui_timeout_ms=16 dxgi_guest_timeout_ms=250 native_acquire_timeout_ns=UINT64_MAX",
           diagnostic_generation_, paint_context_.direct_dxgi ? "direct" : "native",
           cvars::onechanbara_guest_output, is_vsync_implicit_out,
           paint_context_.swapchain_extent.width, paint_context_.swapchain_extent.height);
  }''')
    rep(cc,'Presenter::PaintResult VulkanPresenter::PaintAndPresentImpl(','''bool VulkanPresenter::PreferGuestOutputThreadWithImplicitVsync() const {
  // With diagnostics disabled, retain native Xenia's scheduling policy.
  return cvars::onechanbara_guest_output &&
      (paint_context_.direct_dxgi != nullptr || cvars::onechanbara_diagnostics);
}

Presenter::PaintResult VulkanPresenter::PaintAndPresentImpl(''')
    rep(cc,'''  OcbDisplayStageTimer display_timer(paint_context_.direct_dxgi != nullptr,
      std::this_thread::get_id() == paint_context_.direct_dxgi_ui_thread);''','''  OcbDisplayStageTimer display_timer(diagnostic_cpu_, cvars::onechanbara_diagnostics,
      std::this_thread::get_id() == paint_context_.direct_dxgi_ui_thread,
      paint_context_.direct_dxgi != nullptr);''')
    for name,index in [('command buffer preparation',1),('DXGI acquire',2),('Vulkan image drawing',3),('Vulkan queue submit',4),('DXGI copy and present',5)]:
        rep(cc,'display_timer.Stage("'+name+'");','display_timer.Stage('+str(index)+');')
    rep(cc,'    if (result == OCB_NOT_READY) return PaintResult::kNotPresented;','''    if (cvars::onechanbara_diagnostics) {
      OcbDisplayAcquireTimings t{};
      OcbDisplayGetAcquireTimings(paint_context_.direct_dxgi, &t);
      display_timer.Acquired(t.latency_ms, t.allocator_ms, result);
    }
    if (result == OCB_NOT_READY) return PaintResult::kNotPresented;''')
    rep(cc,'  VkResult acquire_result = dfn.vkAcquireNextImageKHR(','''  display_timer.Stage(2);
  VkResult acquire_result = dfn.vkAcquireNextImageKHR(''')
    rep(cc,'  // Non-zero extents needed for both the viewport (width must not be zero) and','''  display_timer.Stage(3);
  // Non-zero extents needed for both the viewport (width must not be zero) and''')
    rep(cc,'  if (guest_output_image) {','''  if (cvars::onechanbara_diagnostics) {
    display_timer.Frame(guest_output_properties.diagnostic_id,
                        guest_output_properties.diagnostic_publish_ns,
                        DiagnosticProduced());
  }
  if (guest_output_image) {''')
    rep(cc,'  if (execute_ui_drawers) {\n    // Also update the completion timeline','''  display_timer.Submitted();
  if (execute_ui_drawers) {
    // Also update the completion timeline''')
    rep(cc,'  VkPresentInfoKHR present_info;','''  display_timer.Stage(5);
  VkPresentInfoKHR present_info;''')
    rep(cc,'''  switch (present_result) {
    case VK_SUCCESS:
      return PaintResult::kPresented;
    case VK_SUBOPTIMAL_KHR:
      return PaintResult::kPresentedSuboptimal;''','''  switch (present_result) {
    case VK_SUCCESS:
      display_timer.Presented();
      return PaintResult::kPresented;
    case VK_SUBOPTIMAL_KHR:
      display_timer.Presented();
      return PaintResult::kPresentedSuboptimal;''')
    rep(bh,'  VkBool32 timeline_enabled;','''  VkBool32 timeline_enabled;
  bool diagnostics = false;''')
    rep(bh,'struct OcbDisplayFrame {','''struct OcbDisplayAcquireTimings { double latency_ms, allocator_ms; };
struct OcbDisplayFrame {''')
    rep(bh,'OCB_DISPLAY_API int OcbDisplayGetImages(','''OCB_DISPLAY_API void OcbDisplayGetAcquireTimings(void*, OcbDisplayAcquireTimings*);
OCB_DISPLAY_API int OcbDisplayGetImages(''')
    rep(bc,'    swap_ready_ = true;','''    swap_ready_ = true;
    swap_.diagnostics = c.diagnostics;''')
    rep(bc,'  int Acquire(OcbDisplayFrame* out, uint32_t timeout) {','''  void AcquireTimings(OcbDisplayAcquireTimings* t) const {
    if (t) { t->latency_ms = swap_.diagnostic_latency_ms;
             t->allocator_ms = swap_.diagnostic_allocator_ms; }
  }
  int Acquire(OcbDisplayFrame* out, uint32_t timeout) {''')
    rep(bc,'extern "C" const char* OcbDisplayLastError(void* p) {','''extern "C" void OcbDisplayGetAcquireTimings(void* p, OcbDisplayAcquireTimings* t) {
  if (p) static_cast<Bridge*>(p)->AcquireTimings(t);
}
extern "C" const char* OcbDisplayLastError(void* p) {''')
    rep(vendor,'typedef struct dvk_dxgiSwapChain_t\n{','''#include <chrono>
typedef struct dvk_dxgiSwapChain_t
{
  bool diagnostics = false;
  double diagnostic_latency_ms = 0, diagnostic_allocator_ms = 0;''')
    rep(vendor,'  const DWORD result = WaitForSingleObjectEx( pSwapChain->presentationWaitHandle, timeoutMs, false );','''  std::chrono::steady_clock::time_point diagnostic_began{};
  if (pSwapChain->diagnostics) {
    pSwapChain->diagnostic_latency_ms = pSwapChain->diagnostic_allocator_ms = 0;
    diagnostic_began = std::chrono::steady_clock::now();
  }
  const DWORD result = WaitForSingleObjectEx( pSwapChain->presentationWaitHandle, timeoutMs, false );
  if (pSwapChain->diagnostics) pSwapChain->diagnostic_latency_ms =
      std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-diagnostic_began).count();''')
    rep(vendor,'      HRESULT dxResult = pSwapChain->pFence->SetEventOnCompletion( pFrameResources->lastBlitValue, nullptr );','''      if (pSwapChain->diagnostics) diagnostic_began = std::chrono::steady_clock::now();
      HRESULT dxResult = pSwapChain->pFence->SetEventOnCompletion( pFrameResources->lastBlitValue, nullptr );
      if (pSwapChain->diagnostics) pSwapChain->diagnostic_allocator_ms =
          std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-diagnostic_began).count();''')
