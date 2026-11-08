
#include <cassert>
#include <array>
#include <algorithm>
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
int allocator_failure=0,queue_wait_failure=0,queue_signal_failure=0,present_failure=0;VkResult vk_failure=VK_SUCCESS;
std::vector<std::string> calls;DWORD wait_result=WAIT_OBJECT_0,event_delay=0;
DWORD WaitForSingleObjectEx(void*,DWORD timeout,bool){calls.push_back("latency");return timeout<event_delay?WAIT_TIMEOUT:wait_result;}
struct dvk_result_t{int code=0;const char*message="";};
struct Fence{int id=0;uint64_t completed=0;uint64_t GetCompletedValue(){return completed;}int SetEventOnCompletion(uint64_t v,void*){calls.push_back("allocator_wait:"+std::to_string(id)+":"+std::to_string(v));return allocator_failure;}};
struct Allocator{int Reset(){calls.push_back("allocator_reset");return 0;}};
constexpr int D3D12_RESOURCE_BARRIER_TYPE_TRANSITION=0,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES=0,D3D12_RESOURCE_STATE_PRESENT=0,D3D12_RESOURCE_STATE_COPY_DEST=1,D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX=0;
struct D3D12_RESOURCE_BARRIER{int Type;struct{int Subresource;void*pResource;int StateBefore,StateAfter;}Transition;};
struct D3D12_TEXTURE_COPY_LOCATION{int Type;int SubresourceIndex;void*pResource;};
struct ID3D12CommandList{};
struct CommandList:ID3D12CommandList{
 int Reset(Allocator*,void*){calls.push_back("list_reset");return 0;}
 void ResourceBarrier(int,D3D12_RESOURCE_BARRIER*b){calls.push_back("barrier:"+std::to_string(b->Transition.StateAfter));}
 void CopyTextureRegion(D3D12_TEXTURE_COPY_LOCATION*,int,int,int,D3D12_TEXTURE_COPY_LOCATION*src,void*){calls.push_back("copy_source:"+std::to_string(reinterpret_cast<uintptr_t>(src->pResource)));}
 int Close(){calls.push_back("list_close");return 0;}
};
struct Queue{
 int Wait(Fence*f,uint64_t v){calls.push_back("wait_render:"+std::to_string(f->id)+":"+std::to_string(v));return queue_wait_failure;}
 void ExecuteCommandLists(int,ID3D12CommandList**){calls.push_back("execute_copy");}
 int Signal(Fence*f,uint64_t v){calls.push_back("signal_copy:"+std::to_string(f->id)+":"+std::to_string(v));return queue_signal_failure;}
};
constexpr int DXGI_PRESENT_ALLOW_TEARING=512;
struct Swap{uint32_t index=0;uint32_t GetCurrentBackBufferIndex(){return index;}
 int Present(uint32_t interval,UINT flags){calls.push_back("present:"+std::to_string(interval)+":"+std::to_string(flags));return present_failure;}};
struct Image{void*pImage=nullptr;};
struct Device{Queue*pCommandQueue;CommandList*pCommandList;};
struct dvk_perFrameResources_t{uint64_t lastSubmitValue=0,lastBlitValue=0;Allocator*pCommandAllocator=nullptr;Image sharedImage;Image blitImage;VkImage vkBlitImage{};};
using dvk_swapChainFlags_e=uint32_t;constexpr uint32_t DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG=1,DVK_SWAPCHAIN_ALLOW_TEARING_FLAG=2;
bool __dvk_hasSwapChainFlag(uint32_t flags,uint32_t bit){return (flags&bit)!=0;}
struct dvk_dxgiSwapChain_t{void*presentationWaitHandle=nullptr;Swap*pSwapChain;dvk_perFrameResources_t*pPerFrameResources;uint32_t flags=1;Fence*pFence;Device*pDeviceContext;uint64_t fenceValue=0;VkSemaphore semaphore{};uint32_t syncInterval=1;Fence*pCopyFence;VkSemaphore copySemaphore{};};
struct dvk_presentationInfo_t{Swap*pSwapChain=nullptr;Queue*pCommandQueue=nullptr;CommandList*pCommandList=nullptr;dvk_perFrameResources_t*pFrameResources=nullptr;Fence*pFence=nullptr;Fence*pCopyFence=nullptr;uint32_t imageIndex=0;VkSemaphore waitSemaphore{};uint64_t waitValue=0;VkSemaphore submitSemaphore{};uint64_t submitValue=0,blitValue=0;bool allowTearing=false;uint32_t syncInterval=1;};
struct dvk_presentParameters_t{Swap*pSwapChain=nullptr;Queue*pCommandQueue=nullptr;CommandList*pCommandList=nullptr;dvk_perFrameResources_t*pFrameResources=nullptr;Fence*pFence=nullptr;Fence*pCopyFence=nullptr;uint64_t submitValue=0,blitValue=0;uint32_t syncInterval=1;bool allowTearing=false;};
struct OcbDisplayFrame{VkImage image;uint32_t image_index;uint64_t signal_value;VkImageMemoryBarrier acquire_barrier,release_barrier;};

VkSemaphore expected_wait_sem{},expected_signal_sem{};uint64_t last_vk_wait=999,last_vk_signal=999;
VkResult MockSubmit(VkQueue,uint32_t count,const VkSubmitInfo*si,VkFence){
 assert(count==1 && si->waitSemaphoreCount==1 && si->signalSemaphoreCount==1);
 assert(*si->pWaitSemaphores==expected_wait_sem && *si->pSignalSemaphores==expected_signal_sem);
 assert(*si->pWaitDstStageMask==VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
 auto ti=static_cast<const VkTimelineSemaphoreSubmitInfo*>(si->pNext);
 last_vk_wait=*ti->pWaitSemaphoreValues;last_vk_signal=*ti->pSignalSemaphoreValues;
 calls.push_back("vk_submit");return vk_failure;
}
static dvk_result_t dvk_acquireImage( dvk_dxgiSwapChain_t * pSwapChain, dvk_presentationInfo_t * pPresentationInfo, DWORD timeoutMs ) noexcept
{
  if ( pPresentationInfo == nullptr )
  {
    return dvk_result_t{ .code = DVK_ERROR, .message = DVK_PREPEND( "Presentation info cannot be null" ) };
  }

  const DWORD result = WaitForSingleObjectEx( pSwapChain->presentationWaitHandle, timeoutMs, false );
  if ( result != WAIT_OBJECT_0 )
  {
    if ( result == WAIT_TIMEOUT )
    {
      return dvk_result_t{ .code = DVK_NOT_READY, .message = DVK_PREPEND( "Presentation event is not ready" ) };
    }
    return dvk_result_t{ .code = DVK_ERROR, .message = DVK_PREPEND( "Error while waiting for the presentation event" ) };
  }

  const uint32_t imageIndex = pSwapChain->pSwapChain->GetCurrentBackBufferIndex();

  dvk_perFrameResources_t * pFrameResources = &pSwapChain->pPerFrameResources[imageIndex];

  uint64_t waitFenceValue   = 0;
  uint64_t submitFenceValue = 0;
  uint64_t blitFenceValue   = 0;

  if ( __dvk_hasSwapChainFlag( pSwapChain->flags, DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG ) )
  {
    if ( pFrameResources->lastBlitValue != 0 && pSwapChain->pCopyFence->GetCompletedValue() < pFrameResources->lastBlitValue )
    {
      HRESULT dxResult = pSwapChain->pCopyFence->SetEventOnCompletion( pFrameResources->lastBlitValue, nullptr );
      if ( FAILED( dxResult ) )
      {
        return dvk_result_t{ .code = DVK_ERROR_DX12, .message = DVK_PREPEND( "Error waiting for the blit fence to be signaled" ) };
      }
    }

    HRESULT dxResult = pFrameResources->pCommandAllocator->Reset();
    if ( FAILED( dxResult ) )
    {
      return dvk_result_t{ .code = DVK_ERROR_DX12, .message = DVK_PREPEND( "Failed to reset the frame command allocator" ) };
    }

    dxResult = pSwapChain->pDeviceContext->pCommandList->Reset( pFrameResources->pCommandAllocator, nullptr );
    if ( FAILED( dxResult ) )
    {
      return dvk_result_t{ .code = DVK_ERROR_DX12, .message = DVK_PREPEND( "Failed to reset the command list" ) };
    }

    D3D12_RESOURCE_BARRIER barrier = {};
    barrier.Type                   = D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
    barrier.Transition.Subresource = D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
    barrier.Transition.pResource   = pFrameResources->sharedImage.pImage;
    barrier.Transition.StateBefore = D3D12_RESOURCE_STATE_PRESENT;
    barrier.Transition.StateAfter  = D3D12_RESOURCE_STATE_COPY_DEST;
    pSwapChain->pDeviceContext->pCommandList->ResourceBarrier( 1, &barrier );

    D3D12_TEXTURE_COPY_LOCATION dst = {}, src = {};
    dst.Type      = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
    src.Type      = D3D12_TEXTURE_COPY_TYPE_SUBRESOURCE_INDEX;
    dst.pResource = pFrameResources->sharedImage.pImage;
    src.pResource = pFrameResources->blitImage.pImage;
    pSwapChain->pDeviceContext->pCommandList->CopyTextureRegion( &dst, 0, 0, 0, &src, nullptr );

    barrier.Transition.StateBefore = D3D12_RESOURCE_STATE_COPY_DEST;
    barrier.Transition.StateAfter  = D3D12_RESOURCE_STATE_PRESENT;
    pSwapChain->pDeviceContext->pCommandList->ResourceBarrier( 1, &barrier );

    dxResult = pSwapChain->pDeviceContext->pCommandList->Close();
    if ( FAILED( dxResult ) )
    {
      return dvk_result_t{
        .code    = DVK_ERROR_DX12,
        .message = DVK_PREPEND( "Failed to close the command list" ),
      };
    }

    // Reuse only this slot's image. Other slots may render while D3D12 copies.
    // Equal values on TWO distinct timelines cannot signal each other early.
    waitFenceValue   = pFrameResources->lastBlitValue;
    submitFenceValue = ++pSwapChain->fenceValue;
    blitFenceValue   = submitFenceValue;
  }
  else
  {
    // When sharing the memory, the synchronization is parallel: each present waits on its own back buffer
    waitFenceValue                   = pFrameResources->lastSubmitValue;
    submitFenceValue                 = ++pSwapChain->fenceValue;
    pFrameResources->lastSubmitValue = submitFenceValue;
  }

  *pPresentationInfo = dvk_presentationInfo_t{ .pSwapChain      = pSwapChain->pSwapChain,
                                               .pCommandQueue   = pSwapChain->pDeviceContext->pCommandQueue,
                                               .pCommandList    = __dvk_hasSwapChainFlag( pSwapChain->flags, DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG )
                                                                  ? pSwapChain->pDeviceContext->pCommandList
                                                                  : nullptr,
                                               .pFrameResources = pFrameResources,
                                               .pFence          = pSwapChain->pFence,
                                               .pCopyFence      = pSwapChain->pCopyFence,
                                               .imageIndex      = imageIndex,
                                               .waitSemaphore   = pSwapChain->pCopyFence ? pSwapChain->copySemaphore : pSwapChain->semaphore,
                                               .waitValue       = waitFenceValue,
                                               .submitSemaphore = pSwapChain->semaphore,
                                               .submitValue     = submitFenceValue,
                                               .blitValue       = blitFenceValue,
                                               .allowTearing    = __dvk_hasSwapChainFlag( pSwapChain->flags, DVK_SWAPCHAIN_ALLOW_TEARING_FLAG ),
                                               .syncInterval    = pSwapChain->syncInterval };

  return dvk_result_t{ .code = DVK_OK };
}
static dvk_result_t dvk_presentImage( const dvk_presentParameters_t & presentParameters ) noexcept
{
  HRESULT result = presentParameters.pCommandQueue->Wait( presentParameters.pFence, presentParameters.submitValue );
  if ( FAILED( result ) )
  {
    return dvk_result_t{ .code = DVK_ERROR_DX12, .message = DVK_PREPEND( "Failed to wait for the VK submit fence" ) };
  }

  // A non null command list here means that we are doing a blit to back buffer
  if ( presentParameters.pCommandList != nullptr )
  {
    presentParameters.pCommandQueue->ExecuteCommandLists( 1, ( (ID3D12CommandList **)&presentParameters.pCommandList ) );

    result = presentParameters.pCommandQueue->Signal( presentParameters.pCopyFence, presentParameters.blitValue );
    if ( FAILED( result ) )
    {
      return dvk_result_t{ .code = DVK_ERROR_DX12, .message = DVK_PREPEND( "Failed to signal the blit fence" ) };
    }
  }
  presentParameters.pFrameResources->lastBlitValue = presentParameters.blitValue;

  const bool vsyncEnabled = presentParameters.syncInterval != 0;
  const UINT flags        = ( !vsyncEnabled && presentParameters.allowTearing ) ? DXGI_PRESENT_ALLOW_TEARING : 0x0;

  result = presentParameters.pSwapChain->Present( presentParameters.syncInterval, flags );
  if ( FAILED( result ) )
  {
    return dvk_result_t{ .code = DVK_ERROR_DX12, .message = DVK_PREPEND( "Failed to present the swap chain buffer" ) };
  }

  return dvk_result_t{ .code = DVK_OK };
}

struct Probe {
using FrameState=ocb::display::FrameState;ocb::display::FrameContract contract_;
dvk_dxgiSwapChain_t swap_{};dvk_presentationInfo_t pending_{};bool swap_ready_=true;
std::array<bool,3> shared_image_initialized_{};
struct{uint32_t queue_family=1;VkQueue queue{};}c_;
PFN_vkQueueSubmit submit_=MockSubmit;
bool Error(const char*){return false;}bool Check(dvk_result_t r){return r.code==DVK_OK;}
  int Acquire(OcbDisplayFrame* out, uint32_t timeout) {
    if (!out || timeout > 250 || contract_.state() != FrameState::Idle) {
      Error("Acquire requires idle state and a timeout of 0..250 ms."); return OCB_ERROR;
    }
    auto r = dvk_acquireImage(&swap_, &pending_, timeout);
    if (r.code == DVK_NOT_READY) return OCB_NOT_READY;
    if (!Check(r)) { contract_.Fail(); return OCB_ERROR; }
    if (!contract_.Acquire(pending_.imageIndex, pending_.waitValue,
                           pending_.submitValue)) {
      contract_.Fail(); Error("Invalid image index or non-monotonic shared fence value.");
      return OCB_ERROR;
    }
    if (pending_.blitValue != pending_.submitValue ||
        !swap_.pPerFrameResources[pending_.imageIndex].vkBlitImage ||
        pending_.waitSemaphore == pending_.submitSemaphore) {
      contract_.Fail(); Error("Invalid shared-image copy timeline."); return OCB_ERROR;
    }
    auto image = swap_.pPerFrameResources[pending_.imageIndex].vkBlitImage;
    *out = {image, pending_.imageIndex, pending_.submitValue,
        ocb::display::AcquireBarrier(image, c_.queue_family, shared_image_initialized_[pending_.imageIndex]),
        ocb::display::ReleaseBarrier(image, c_.queue_family)};
    return OCB_OK;
  }
  int Submit(const OcbDisplayFrame* frame, VkCommandBuffer cmd, VkFence fence) {
    if (!frame || !cmd || contract_.state() != FrameState::Acquired ||
        frame->image_index != pending_.imageIndex ||
        frame->signal_value != pending_.submitValue ||
        frame->image != swap_.pPerFrameResources[pending_.imageIndex].vkBlitImage) {
      Error("Submit rejected: no acquired frame or a stale frame token."); return OCB_ERROR;
    }
    VkTimelineSemaphoreSubmitInfo ti{VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO};
    ti.waitSemaphoreValueCount = 1; ti.pWaitSemaphoreValues = &pending_.waitValue;
    ti.signalSemaphoreValueCount = 1; ti.pSignalSemaphoreValues = &pending_.submitValue;
    const VkPipelineStageFlags wait_stage = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
    VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    si.pNext = &ti; si.waitSemaphoreCount = 1;
    si.pWaitSemaphores = &pending_.waitSemaphore; si.pWaitDstStageMask = &wait_stage;
    si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
    si.signalSemaphoreCount = 1; si.pSignalSemaphores = &pending_.submitSemaphore;
    auto vr = submit_(c_.queue, 1, &si, fence);
    if (vr != VK_SUCCESS) {
      contract_.Fail(); Error("Vulkan submit failed; display bridge stopped."); return OCB_ERROR;
    }
    return PresentSubmitted(frame);
  }
  bool ValidFrame(const OcbDisplayFrame* frame) {
    return frame && contract_.state() == FrameState::Acquired &&
        frame->image_index == pending_.imageIndex &&
        frame->signal_value == pending_.submitValue &&
        frame->image == swap_.pPerFrameResources[pending_.imageIndex].vkBlitImage;
  }
  int GetImages(VkImage* images, uint32_t capacity) {
    if (!images || capacity < 3 || !swap_ready_) return OCB_ERROR;
    for (uint32_t i=0; i<3; ++i) images[i] = swap_.pPerFrameResources[i].vkBlitImage;
    return OCB_OK;
  }
  int GetSync(const OcbDisplayFrame* frame, VkSemaphore* wait_semaphore,
              VkSemaphore* signal_semaphore,
              uint64_t* wait_value, uint64_t* signal_value) {
    if (!ValidFrame(frame) || !wait_semaphore || !signal_semaphore || !wait_value || !signal_value) {
      Error("Invalid synchronization request."); return OCB_ERROR;
    }
    *wait_semaphore = pending_.waitSemaphore;
    *signal_semaphore = pending_.submitSemaphore;
    *wait_value = pending_.waitValue; *signal_value = pending_.submitValue;
    return OCB_OK;
  }
  int PresentSubmitted(const OcbDisplayFrame* frame) {
    if (!ValidFrame(frame)) {
      Error("Stale submitted frame."); return OCB_ERROR;
    }
    contract_.Submit(frame->image_index);
    shared_image_initialized_[pending_.imageIndex] = true;
    dvk_presentParameters_t p{};
    p.pSwapChain = pending_.pSwapChain; p.pCommandQueue = pending_.pCommandQueue;
    p.pCommandList = pending_.pCommandList; p.pFrameResources = pending_.pFrameResources;
    p.pFence = pending_.pFence; p.pCopyFence = pending_.pCopyFence;
    p.submitValue = pending_.submitValue;
    p.blitValue = pending_.blitValue; p.syncInterval = 1; p.allowTearing = false;
    if (!Check(dvk_presentImage(p))) { contract_.Fail(); return OCB_ERROR; }
    contract_.Presented(); return OCB_OK;
  }
  int Cancel() {
    if (!contract_.Cancel()) { Error("Only an unsubmitted frame can be cancelled."); return OCB_ERROR; }
    // Roll back the unused global serial, NOT this slot's older reuse value.
    // Neither GPU timeline has been signaled for this canceled frame.
    swap_.fenceValue = pending_.submitValue - 1;
    return OCB_OK;
  }
};

int main(){
 int checks=0;auto check=[&](bool b){++checks;if(!b){std::fprintf(stderr,"check %d failed\n",checks);std::abort();}};
 Swap swap;Queue queue;CommandList list;Fence render{1},copy{2};Device device{&queue,&list};Allocator allocators[3];dvk_perFrameResources_t resources[3];
 for(int i=0;i<3;++i){resources[i].pCommandAllocator=&allocators[i];resources[i].vkBlitImage=reinterpret_cast<VkImage>(uintptr_t(10+i));resources[i].blitImage.pImage=reinterpret_cast<void*>(uintptr_t(20+i));}
 Probe b;b.swap_.pSwapChain=&swap;b.swap_.pPerFrameResources=resources;b.swap_.pFence=&render;b.swap_.pCopyFence=&copy;b.swap_.pDeviceContext=&device;
 b.swap_.semaphore=expected_signal_sem=reinterpret_cast<VkSemaphore>(uintptr_t(101));
 b.swap_.copySemaphore=expected_wait_sem=reinterpret_cast<VkSemaphore>(uintptr_t(202));
 VkImage images[3]{};check(b.GetImages(images,3)==OCB_OK);check(images[0]!=images[1]&&images[1]!=images[2]&&images[0]!=images[2]);
 check(b.GetImages(images,2)==OCB_ERROR);
 OcbDisplayFrame f{},stale{};VkSemaphore wsem{},ssem{};uint64_t wait=999,signal=999;
 auto cmd=reinterpret_cast<VkCommandBuffer>(uintptr_t(1));
 for(uint32_t slot=0;slot<3;++slot){
  swap.index=slot;calls.clear();check(b.Acquire(&f,250)==OCB_OK);
  check(f.image==images[slot]);check(f.acquire_barrier.oldLayout==VK_IMAGE_LAYOUT_UNDEFINED);
  check(b.GetSync(&f,&wsem,&ssem,&wait,&signal)==OCB_OK);
  check(wsem!=ssem && wsem==expected_wait_sem && ssem==expected_signal_sem);
  // Frames 2 and 3 DO NOT wait for the preceding frame's D3D12 copy.
  check(wait==0 && signal==slot+1 && b.pending_.blitValue==signal);
  check(std::find(calls.begin(),calls.end(),"copy_source:"+std::to_string(20+slot))!=calls.end());
  stale=f;calls.clear();check(b.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_OK);
  check(last_vk_wait==0 && last_vk_signal==slot+1);
  check(calls==std::vector<std::string>{"vk_submit","wait_render:1:"+std::to_string(slot+1),"execute_copy","signal_copy:2:"+std::to_string(slot+1),"present:1:0"});
  check(resources[slot].lastBlitValue==slot+1);
 }
 // Copy fence lagging the render fence must still protect allocator reuse.
 render.completed=99;copy.completed=0;swap.index=0;calls.clear();check(b.Acquire(&f,250)==OCB_OK);
 check(calls[1]=="allocator_wait:2:1");check(f.acquire_barrier.oldLayout==VK_IMAGE_LAYOUT_GENERAL);
 check(b.pending_.waitValue==1 && b.pending_.submitValue==4);
 check(!b.ValidFrame(&stale));check(b.Submit(&stale,cmd,VK_NULL_HANDLE)==OCB_ERROR);
 check(b.Cancel()==OCB_OK);check(b.swap_.fenceValue==3);check(!b.ValidFrame(&f));
 check(b.Acquire(&f,250)==OCB_OK);check(b.pending_.waitValue==1 && b.pending_.submitValue==4);check(b.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_OK);
 // Nonsequential backbuffer selection still waits only for the matching slot.
 swap.index=2;check(b.Acquire(&f,250)==OCB_OK);check(b.pending_.waitValue==3 && b.pending_.submitValue==5);check(b.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_OK);
 swap.index=1;check(b.Acquire(&f,250)==OCB_OK);check(b.pending_.waitValue==2 && b.pending_.submitValue==6);check(b.Cancel()==OCB_OK);check(b.swap_.fenceValue==5);
 auto before=b.swap_.fenceValue;event_delay=33;check(b.Acquire(&f,16)==OCB_NOT_READY);check(b.swap_.fenceValue==before);
 check(b.Acquire(&f,250)==OCB_OK);check(b.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_OK);
 event_delay=50;check(b.Acquire(&f,250)==OCB_OK);check(b.Cancel()==OCB_OK);
 event_delay=300;before=b.swap_.fenceValue;check(b.Acquire(&f,250)==OCB_NOT_READY);check(b.swap_.fenceValue==before);
 check(b.Acquire(&f,251)==OCB_ERROR);check(b.contract_.state()==ocb::display::FrameState::Idle);

 // Real error branches stop the bridge; no later stage runs after a failure.
 event_delay=0;
 {Probe bad=b;allocator_failure=-1;check(bad.Acquire(&f,250)==OCB_ERROR);check(bad.contract_.state()==ocb::display::FrameState::Failed);allocator_failure=0;}
 {Probe bad=b;check(bad.Acquire(&f,250)==OCB_OK);calls.clear();vk_failure=VK_ERROR_DEVICE_LOST;check(bad.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_ERROR);check(calls==std::vector<std::string>{"vk_submit"});check(bad.contract_.state()==ocb::display::FrameState::Failed);vk_failure=VK_SUCCESS;}
 {Probe bad=b;check(bad.Acquire(&f,250)==OCB_OK);calls.clear();queue_wait_failure=-1;check(bad.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_ERROR);check(calls.size()==2);check(bad.contract_.state()==ocb::display::FrameState::Failed);queue_wait_failure=0;}
 {Probe bad=b;check(bad.Acquire(&f,250)==OCB_OK);calls.clear();queue_signal_failure=-1;check(bad.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_ERROR);check(calls.size()==4);check(bad.contract_.state()==ocb::display::FrameState::Failed);queue_signal_failure=0;}
 {Probe bad=b;check(bad.Acquire(&f,250)==OCB_OK);calls.clear();present_failure=-1;check(bad.Submit(&f,cmd,VK_NULL_HANDLE)==OCB_ERROR);check(calls.size()==5);check(bad.contract_.state()==ocb::display::FrameState::Failed);present_failure=0;}
 std::printf("{\"passed\":%d,\"actual_vendor_bridge_and_vk_submit\":true,\"gpu_test\":false,\"mocked\":\"Windows/D3D12/Vulkan objects\"}\n",checks);
}
