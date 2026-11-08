#include <cassert>
#include <vector>
namespace cvars {bool host_present_from_non_ui_thread=true,onechanbara_guest_output=true,onechanbara_diagnostics=false;}
struct Probe { enum class PaintMode {kNone,kUIThreadOnRequest,kGuestOutputThreadImmediately};
 bool surface_paint_connection_has_implicit_vsync_=true;std::vector<int>ui_drawers_;
 struct {void* direct_dxgi=nullptr;}paint_context_;
bool PreferGuestOutputThreadWithImplicitVsync() const {
  // With diagnostics disabled, retain native Xenia's scheduling policy.
  return cvars::onechanbara_guest_output &&
      (paint_context_.direct_dxgi != nullptr || cvars::onechanbara_diagnostics);
}
PaintMode GetDesiredPaintModeFromUIThread(
    bool is_paintable) const {
  if (!is_paintable) {
    // The only case when kNone can be returned, for surface connection updates
    // when it's known that the UI thread currently has access to the connection
    // lifecycle.
    return PaintMode::kNone;
  }
  if (!cvars::host_present_from_non_ui_thread) {
    return PaintMode::kUIThreadOnRequest;
  }
  if (surface_paint_connection_has_implicit_vsync_ &&
      !PreferGuestOutputThreadWithImplicitVsync()) {
    // Don't be causing host vertical sync CPU waits in the thread generating
    // the guest output.
    return PaintMode::kUIThreadOnRequest;
  }
  if (!ui_drawers_.empty()) {
    // The UI can be drawn only by the UI thread, and it needs to be drawn -
    // paint in the UI thread.
    return PaintMode::kUIThreadOnRequest;
  }
  // Only the guest output needs to be drawn - let the guest output thread
  // present immediately for a lower latency.
  return PaintMode::kGuestOutputThreadImmediately;
}
};
int main(){Probe p;using P=Probe::PaintMode;
 assert(p.GetDesiredPaintModeFromUIThread(false)==P::kNone);
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 p.paint_context_.direct_dxgi=&p;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kGuestOutputThreadImmediately);
 cvars::onechanbara_guest_output=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 p.paint_context_.direct_dxgi=nullptr;cvars::onechanbara_guest_output=true;cvars::onechanbara_diagnostics=true;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kGuestOutputThreadImmediately);
 cvars::onechanbara_guest_output=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 cvars::onechanbara_guest_output=true;p.ui_drawers_.push_back(1);
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 p.ui_drawers_.clear();cvars::host_present_from_non_ui_thread=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 cvars::host_present_from_non_ui_thread=true;cvars::onechanbara_diagnostics=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 p.surface_paint_connection_has_implicit_vsync_=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kGuestOutputThreadImmediately);
 p.ui_drawers_.push_back(1);assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
}
