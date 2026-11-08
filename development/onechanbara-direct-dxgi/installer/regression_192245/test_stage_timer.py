from pathlib import Path
import subprocess,json
r=Path(__file__).resolve().parent
s=(r.parent/'xenia_work/src/xenia/ui/vulkan/vulkan_presenter.cc').read_text()
a=s.index('class OcbDisplayStageTimer {');b=s.index('\n};',a)+3
src='''#include <chrono>
#include <thread>
#include <vector>
#include <string>
#include <cassert>
std::vector<std::string> logs;
#define XELOGW(fmt,stage,ms) logs.push_back(stage)
'''+s[a:b]+'''
int main(){
 { OcbDisplayStageTimer t(true);t.Stage("DXGI acquire"); }
 assert(logs.empty());
 { OcbDisplayStageTimer t(false);std::this_thread::sleep_for(std::chrono::milliseconds(120));t.Stage("inactive"); }
 assert(logs.empty());
 { OcbDisplayStageTimer t(true);std::this_thread::sleep_for(std::chrono::milliseconds(120));t.Stage("DXGI copy and present"); }
 assert(logs.size()==1&&logs[0]=="Vulkan completion wait");
 logs.clear();
 { OcbDisplayStageTimer t(true);t.Stage("DXGI copy and present");std::this_thread::sleep_for(std::chrono::milliseconds(120)); }
 assert(logs.size()==1&&logs[0]=="DXGI copy and present");
}
'''
p=r/'stage_timer_test.cc';p.write_text(src)
subprocess.run(['g++','-std=c++20',str(p),'-o',str(r/'stage_timer_test')],check=True)
subprocess.run([str(r/'stage_timer_test')],check=True)
result={'passed':4,'actual_stage_timer':True,'mocked':'Xenia logger','gpu_test':False}
(r/'stage-timer-validation.json').write_text(json.dumps(result,indent=2));print(result)
