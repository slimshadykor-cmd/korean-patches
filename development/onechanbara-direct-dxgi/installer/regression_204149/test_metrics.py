from pathlib import Path
import subprocess,json
r=Path(__file__).resolve().parent
src=(r.parent/'integration/display_metrics.inc').read_text().replace('using Clock = std::chrono::steady_clock;', 'using Clock = FakeClock;')
pre='''#include <chrono>
#include <array>
#include <algorithm>
#include <string>
#include <vector>
#include <cassert>
#include <cstdint>
struct FakeClock {using duration=std::chrono::milliseconds;using time_point=std::chrono::time_point<FakeClock>;static inline int64_t ms=0;static time_point now(){return time_point(duration(ms));}};
struct Entry {std::string thread;double elapsed;uint64_t attempts,presented;double avg,max;std::array<double,12> stages;};
std::vector<Entry> logs;
template<class... T> void log(const char*,const char* thread,double elapsed,uint64_t attempts,uint64_t presented,double avg,double max,T... stages){logs.push_back({thread,elapsed,attempts,presented,avg,max,{double(stages)...}});}
#define XELOGI(...) log(__VA_ARGS__)
'''
post='''int main(){
 {OcbDisplayStageTimer t(false);FakeClock::ms+=2000;}assert(logs.empty());
 for(int i=0;i<50;++i){OcbDisplayStageTimer t(true);FakeClock::ms+=20;t.Presented();}
 assert(logs.size()==1);assert(logs[0].attempts==50&&logs[0].presented==50);
 assert(logs[0].avg==20&&logs[0].max==20&&logs[0].stages[0]==20);
 logs.clear();
 for(int i=0;i<25;++i){
  OcbDisplayStageTimer t(true);FakeClock::ms+=1;t.Stage("preparation");t.Stage("acquire");
  FakeClock::ms+=33;t.Stage("drawing");FakeClock::ms+=2;t.Stage("submit");t.Stage("present");
  FakeClock::ms+=5;if(i!=4)t.Presented();
 }
 assert(logs.size()==1);assert(logs[0].elapsed==1025&&logs[0].attempts==25&&logs[0].presented==24);
 assert(logs[0].avg==41&&logs[0].max==41&&logs[0].stages[4]==33&&logs[0].stages[10]==5);
 logs.clear();{OcbDisplayStageTimer t(true,true);FakeClock::ms+=1500;}
 assert(logs.size()==1&&logs[0].thread=="UI"&&logs[0].presented==0&&logs[0].max==1500);
}
'''
(r/'metrics_test.cc').write_text(pre+src+post)
subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',str(r/'metrics_test.cc'),'-o',str(r/'metrics_test')],check=True)
subprocess.run([str(r/'metrics_test')],check=True)
result={'passed':9,'actual_timer':True,'mocked':'monotonic clock and logger','gpu_test':False,'cases':['20 ms frames below old threshold','33 ms acquire','41 ms total','not-presented attempts counted separately','one-second log aggregation','UI thread annotation','1500 ms stall']}
(r/'metrics-validation.json').write_text(json.dumps(result,indent=2));print(result)
