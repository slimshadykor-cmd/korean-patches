from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent;root=R.parent/'generator/non_nv';bridge_root=root/'xenia_work/src/xenia/ui/vulkan/onechanbara_display'
vendor=(bridge_root/'vendor/vk_dxgi.h').read_text();bridge=(bridge_root/'vulkan_dxgi_bridge.cc').read_text()
def function(s,marker):
 start=s.index(marker);a=s.index('{',start);depth=1;i=a+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[start:i]
acquire=function(vendor,'static dvk_result_t dvk_acquireImage( dvk_dxgiSwapChain_t * pSwapChain, dvk_presentationInfo_t * pPresentationInfo, DWORD timeoutMs ) noexcept\n')
present=function(vendor,'static dvk_result_t dvk_presentImage( const dvk_presentParameters_t & presentParameters ) noexcept\n')
methods='\n'.join(function(bridge,m) for m in ['  int Acquire(', '  bool ValidFrame(', '  int GetImages(', '  int GetSync(', '  int PresentSubmitted(', '  int Cancel('])
pre=r'''
#include <cassert>
#include <chrono>
#include <cstdint>
#include <string>
#include <vector>
#include <cstdio>
#include "frame_contract.h"
using DWORD=uint32_t;using UINT=uint32_t;using HRESULT=int;
constexpr int WAIT_OBJECT_0=0,WAIT_TIMEOUT=258,DVK_OK=0,DVK_NOT_READY=-1,DVK_ERROR=1,DVK_ERROR_DX12=2;
constexpr int OCB_ERROR=-1,OCB_OK=0,OCB_NOT_READY=1;
#define FAILED(x) ((x)<0)
#define DVK_PREPEND(x) x
std::vector<std::string> calls;DWORD wait_result=WAIT_OBJECT_0,event_delay=0;
DWORD WaitForSingleObjectEx(void*,DWORD timeout,bool){calls.push_back("latency");return timeout<event_delay?WAIT_TIMEOUT:wait_result;}
struct dvk_result_t{int code=0;const char*message="";};
struct Fence{uint64_t completed=0;uint64_t GetCompletedValue(){return completed;}int SetEventOnCompletion(uint64_t v,void*){calls.push_back("allocator_wait:"+std::to_string(v));return 0;}};
struct Allocator{int Reset(){calls.push_back("allocator_reset");return 0;}};
constexpr int D3D12_RESOURCE_BARRIER_TYPE_TRANSITION=0,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES=0,D3D12_RESOURCE_STATE_PRESENT=0,D3D12_RESOURCE_STATE_COPY_DEST=1,D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX=0;
struct D3D12_RESOURCE_BARRIER{int Type;struct{int Subresource;void*pResource;int StateBefore,StateAfter;}Transition;};
struct D3D12_TEXTURE_COPY_LOCATION{int Type;int SubresourceIndex;void*pResource;};
struct ID3D12CommandList{};
struct CommandList:ID3D12CommandList{
 int Reset(Allocator*,void*){calls.push_back("list_reset");return 0;}
 void ResourceBarrier(int,D3D12_RESOURCE_BARRIER*b){calls.push_back("barrier:"+std::to_string(b->Transition.StateAfter));}
 void CopyTextureRegion(D3D12_TEXTURE_COPY_LOCATION*,int,int,int,D3D12_TEXTURE_COPY_LOCATION*,void*){calls.push_back("record_copy");}
 int Close(){calls.push_back("list_close");return 0;}
};
struct Queue{
 int Wait(Fence*,uint64_t v){calls.push_back("wait_render:"+std::to_string(v));return 0;}
 void ExecuteCommandLists(int,ID3D12CommandList**){calls.push_back("execute_copy");}
 int Signal(Fence*,uint64_t v){calls.push_back("signal_copy:"+std::to_string(v));return 0;}
};
constexpr int DXGI_PRESENT_ALLOW_TEARING=512;
struct Swap{uint32_t index=0;uint32_t GetCurrentBackBufferIndex(){return index;}
 int Present(uint32_t interval,UINT flags){calls.push_back("present:"+std::to_string(interval)+":"+std::to_string(flags));return 0;}};
struct Image{void*pImage=nullptr;};
struct Device{Queue*pCommandQueue;CommandList*pCommandList;};
struct dvk_perFrameResources_t{uint64_t lastSubmitValue=0,lastBlitValue=0;Allocator*pCommandAllocator=nullptr;Image sharedImage;};
using dvk_swapChainFlags_e=uint32_t;constexpr uint32_t DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG=1,DVK_SWAPCHAIN_ALLOW_TEARING_FLAG=2;
bool __dvk_hasSwapChainFlag(uint32_t flags,uint32_t bit){return (flags&bit)!=0;}
struct dvk_dxgiSwapChain_t{void*presentationWaitHandle=nullptr;Swap*pSwapChain;dvk_perFrameResources_t*pPerFrameResources;uint32_t flags=1;Fence*pFence;Device*pDeviceContext;Image pBlitImage;uint64_t fenceValue=0;VkSemaphore semaphore{};uint32_t syncInterval=1;VkImage vkBlitImage{};bool diagnostics=true;double diagnostic_latency_ms=0,diagnostic_allocator_ms=0;};
struct dvk_presentationInfo_t{Swap*pSwapChain=nullptr;Queue*pCommandQueue=nullptr;CommandList*pCommandList=nullptr;dvk_perFrameResources_t*pFrameResources=nullptr;Fence*pFence=nullptr;uint32_t imageIndex=0;VkSemaphore waitSemaphore{};uint64_t waitValue=0;VkSemaphore submitSemaphore{};uint64_t submitValue=0,blitValue=0;bool allowTearing=false;uint32_t syncInterval=1;};
struct dvk_presentParameters_t{Swap*pSwapChain=nullptr;Queue*pCommandQueue=nullptr;CommandList*pCommandList=nullptr;dvk_perFrameResources_t*pFrameResources=nullptr;Fence*pFence=nullptr;uint64_t submitValue=0,blitValue=0;uint32_t syncInterval=1;bool allowTearing=false;};
struct OcbDisplayFrame{VkImage image;uint32_t image_index;uint64_t signal_value;VkImageMemoryBarrier acquire_barrier,release_barrier;};
'''
post=r'''
int main(){
 int checks=0;auto check=[&](bool b){++checks;if(!b){std::fprintf(stderr,"check %d failed\n",checks);std::abort();}};
 Swap swap;Queue queue;CommandList list;Fence fence;Device device{&queue,&list};Allocator allocators[3];dvk_perFrameResources_t resources[3];
 for(int i=0;i<3;++i)resources[i].pCommandAllocator=&allocators[i];
 Probe b;b.swap_={nullptr,&swap,resources,1,&fence,&device,{},0,{},1,reinterpret_cast<VkImage>(uintptr_t{9})};
 VkImage images[3]{};check(b.GetImages(images,3)==OCB_OK);check(images[0]==images[1]&&images[1]==images[2]&&images[0]==b.swap_.vkBlitImage);
 OcbDisplayFrame f{};VkSemaphore sem{};uint64_t wait=99,signal=99;
 check(b.Acquire(&f,16)==OCB_OK);check(f.image==images[0]);check(f.acquire_barrier.oldLayout==VK_IMAGE_LAYOUT_UNDEFINED);
 check(b.GetSync(&f,&sem,&wait,&signal)==OCB_OK);check(wait==0&&signal==1&&b.pending_.blitValue==2);
 calls.clear();check(b.PresentSubmitted(&f)==OCB_OK);
 check(calls==std::vector<std::string>{"wait_render:1","execute_copy","signal_copy:2","present:1:0"});
 swap.index=1;check(b.Acquire(&f,16)==OCB_OK);check(f.image==images[0]);check(f.acquire_barrier.oldLayout==VK_IMAGE_LAYOUT_GENERAL);
 check(b.GetSync(&f,&sem,&wait,&signal)==OCB_OK);check(wait==2&&signal==3&&b.pending_.blitValue==4);
 check(b.Cancel()==OCB_OK);check(b.swap_.fenceValue==2);check(!b.ValidFrame(&f));
 check(b.Acquire(&f,16)==OCB_OK);check(b.pending_.waitValue==2&&b.pending_.submitValue==3&&b.pending_.blitValue==4);
 check(b.PresentSubmitted(&f)==OCB_OK);
 swap.index=2;check(b.Acquire(&f,16)==OCB_OK);check(b.pending_.waitValue==4&&b.pending_.submitValue==5&&b.pending_.blitValue==6);
 check(b.PresentSubmitted(&f)==OCB_OK);
 swap.index=0;calls.clear();check(b.Acquire(&f,16)==OCB_OK);check(calls.size()>1&&calls[1]=="allocator_wait:2");
 check(b.pending_.waitValue==6&&b.pending_.submitValue==7&&b.pending_.blitValue==8);
 check(b.Cancel()==OCB_OK);wait_result=WAIT_TIMEOUT;auto before=b.swap_.fenceValue;
 check(b.Acquire(&f,16)==OCB_NOT_READY);check(b.swap_.fenceValue==before);check(b.contract_.state()==ocb::display::FrameState::Idle);
 wait_result=WAIT_OBJECT_0;check(b.Acquire(&f,16)==OCB_OK);check(b.pending_.waitValue==6);check(b.PresentSubmitted(&f)==OCB_OK);
 event_delay=33;before=b.swap_.fenceValue;
 check(b.Acquire(&f,16)==OCB_NOT_READY);check(b.swap_.fenceValue==before);
 check(b.Acquire(&f,250)==OCB_OK);check(b.pending_.waitValue==before);check(b.PresentSubmitted(&f)==OCB_OK);
 event_delay=50;check(b.Acquire(&f,250)==OCB_OK);check(b.Cancel()==OCB_OK);
 event_delay=300;before=b.swap_.fenceValue;check(b.Acquire(&f,250)==OCB_NOT_READY);check(b.swap_.fenceValue==before);
 check(b.Acquire(&f,251)==OCB_ERROR);
 std::printf("{\"passed\":%d,\"actual_vendor_and_bridge_methods\":true,\"gpu_test\":false,\"mocked\":\"Windows/D3D12/Vulkan objects and OS events\"}\n",checks);
}
'''
probe='''\nstruct Probe {\nusing FrameState=ocb::display::FrameState;ocb::display::FrameContract contract_;dvk_dxgiSwapChain_t swap_{};dvk_presentationInfo_t pending_{};bool swap_ready_=true,shared_image_initialized_=false;struct{uint32_t queue_family=1;}c_;bool Error(const char*){return false;}bool Check(dvk_result_t r){return r.code==DVK_OK;}\n'''+methods+'\n};\n'
file=R/'copy_protocol_test.cc';file.write_text(pre+acquire+'\n'+present+'\n'+probe+post)
subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(bridge_root),'-I'+str(root/'dependencies/Vulkan-Headers-1.3.296/include'),str(file),'-o',str(R/'copy_protocol_test')],check=True)
r=subprocess.run([str(R/'copy_protocol_test')],check=True,capture_output=True,text=True)
(R/'copy-protocol-validation.json').write_text(r.stdout);print(r.stdout)
