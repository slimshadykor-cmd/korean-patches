from pathlib import Path
import subprocess,json
r=Path(__file__).resolve().parent
src=(r.parent/'xenia_work/src/xenia/ui/presenter.cc').read_text()
a=src.index('Presenter::PaintMode Presenter::GetDesiredPaintModeFromUIThread(')
b=src.index('\nvoid Presenter::DisconnectPaintingFromSurfaceFromUIThread',a)
method=src[a:b].replace('Presenter::PaintMode Presenter::','PaintMode ')
program='''#include <cassert>
#include <vector>
namespace cvars {bool host_present_from_non_ui_thread=true;}
struct Probe {
 enum class PaintMode {kNone,kUIThreadOnRequest,kGuestOutputThreadImmediately};
 bool surface_paint_connection_has_implicit_vsync_=true,bridge=false;
 std::vector<int> ui_drawers_;
 bool PreferGuestOutputThreadWithImplicitVsync() const{return bridge;}
'''+method+'''};
int main(){
 Probe p;using P=Probe::PaintMode;
 assert(p.GetDesiredPaintModeFromUIThread(false)==P::kNone);
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 p.bridge=true;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kGuestOutputThreadImmediately);
 p.ui_drawers_.push_back(1);
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 p.ui_drawers_.clear();cvars::host_present_from_non_ui_thread=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
 cvars::host_present_from_non_ui_thread=true;p.bridge=false;p.surface_paint_connection_has_implicit_vsync_=false;
 assert(p.GetDesiredPaintModeFromUIThread(true)==P::kGuestOutputThreadImmediately);
 p.ui_drawers_.push_back(1);assert(p.GetDesiredPaintModeFromUIThread(true)==P::kUIThreadOnRequest);
}
'''
(r/'pacing_test.cc').write_text(program)
subprocess.run(['g++','-std=c++20',str(r/'pacing_test.cc'),'-o',str(r/'pacing_test')],check=True)
subprocess.run([str(r/'pacing_test')],check=True)
result={'passed':7,'actual_presenter_policy':True,'mocked':'cvars, painting state, and UI drawer list','gpu_test':False}
(r/'pacing-validation.json').write_text(json.dumps(result,indent=2));print(result)
