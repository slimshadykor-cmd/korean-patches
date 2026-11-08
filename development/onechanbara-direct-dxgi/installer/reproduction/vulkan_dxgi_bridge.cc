#define OCB_DISPLAY_BUILD
#ifndef VK_NO_PROTOTYPES
#define VK_NO_PROTOTYPES
#endif
#include "vulkan_dxgi_bridge.h"
#include "frame_contract.h"
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstring>
#include <malloc.h>
#include <new>
#include <vector>
#define DX_SWAP_VK_IMPLEMENTATION
#include "vendor/vk_dxgi.h"

namespace {
using ocb::display::FrameContract;
using ocb::display::FrameState;
constexpr const char* kExtensions[] = {
    VK_KHR_EXTERNAL_MEMORY_WIN32_EXTENSION_NAME,
    VK_KHR_EXTERNAL_SEMAPHORE_WIN32_EXTENSION_NAME};

class Bridge {
 public:
  ~Bridge() {
    if (swap_ready_) dvk_destroySwapChain(&swap_);
    if (device_ready_) dvk_destroyDevice(dx_);
    if (d3d12_) FreeLibrary(d3d12_);
    if (dxgi_) FreeLibrary(dxgi_);
  }
  bool Error(const char* msg) {
    std::snprintf(error_, sizeof(error_), "%s", msg); return false;
  }
  bool Check(dvk_result_t result) {
    return !dvk_isError(result) || Error(result.message);
  }
  bool Initialize(const OcbDisplayConfig& c) {
    c_ = c;
    if (!c.instance || !c.physical_device || !c.device || !c.queue ||
        !c.get_instance_proc || !c.get_device_proc || !IsWindow(c.window) ||
        !c.width || !c.height || c.width > 65535 || c.height > 65535 ||
        !c.timeline_enabled || !c.enabled_extensions)
      return Error("Invalid context, extent or enabled timeline feature.");
    for (auto name : kExtensions) {
      bool enabled = false;
      for (uint32_t i = 0; i < c.enabled_extension_count; ++i)
        enabled |= c.enabled_extensions[i] &&
                   std::strcmp(name, c.enabled_extensions[i]) == 0;
      if (!enabled) return Error("Required Win32 sharing extension is not enabled.");
    }
    auto props = reinterpret_cast<PFN_vkGetPhysicalDeviceProperties2>(
        c.get_instance_proc(c.instance, "vkGetPhysicalDeviceProperties2"));
    auto features = reinterpret_cast<PFN_vkGetPhysicalDeviceFeatures2>(
        c.get_instance_proc(c.instance, "vkGetPhysicalDeviceFeatures2"));
    auto image_props = reinterpret_cast<PFN_vkGetPhysicalDeviceImageFormatProperties2>(
        c.get_instance_proc(c.instance, "vkGetPhysicalDeviceImageFormatProperties2"));
    auto sem_props = reinterpret_cast<PFN_vkGetPhysicalDeviceExternalSemaphoreProperties>(
        c.get_instance_proc(c.instance, "vkGetPhysicalDeviceExternalSemaphoreProperties"));
    auto families = reinterpret_cast<PFN_vkGetPhysicalDeviceQueueFamilyProperties>(
        c.get_instance_proc(c.instance, "vkGetPhysicalDeviceQueueFamilyProperties"));
    if (!props || !features || !image_props || !sem_props || !families)
      return Error("Required Vulkan capability queries unavailable.");
    VkPhysicalDeviceIDProperties id{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES};
    VkPhysicalDeviceProperties2 p{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2};
    p.pNext = &id; props(c.physical_device, &p);
    if (p.properties.apiVersion < VK_API_VERSION_1_2 || !id.deviceLUIDValid ||
        id.deviceNodeMask != 1)
      return Error("This candidate requires Vulkan 1.2 and a valid single-node adapter LUID.");
    VkPhysicalDeviceTimelineSemaphoreFeatures tf{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES};
    VkPhysicalDeviceFeatures2 f{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
    f.pNext = &tf; features(c.physical_device, &f);
    if (!tf.timelineSemaphore) return Error("Timeline semaphores are unsupported.");
    uint32_t family_count = 0;
    families(c.physical_device, &family_count, nullptr);
    std::vector<VkQueueFamilyProperties> qp(family_count);
    families(c.physical_device, &family_count, qp.data());
    if (c.queue_family >= family_count ||
        !(qp[c.queue_family].queueFlags & VK_QUEUE_GRAPHICS_BIT))
      return Error("A graphics queue family is required.");

    VkPhysicalDeviceExternalImageFormatInfo ei{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_IMAGE_FORMAT_INFO};
    ei.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_D3D12_RESOURCE_BIT;
    VkPhysicalDeviceImageFormatInfo2 ii{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2};
    ii.pNext = &ei; ii.format = VK_FORMAT_R8G8B8A8_UNORM;
    ii.type = VK_IMAGE_TYPE_2D; ii.tiling = VK_IMAGE_TILING_OPTIMAL;
    ii.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
    VkExternalImageFormatProperties eo{VK_STRUCTURE_TYPE_EXTERNAL_IMAGE_FORMAT_PROPERTIES};
    VkImageFormatProperties2 io{VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2};
    io.pNext = &eo;
    if (image_props(c.physical_device, &ii, &io) != VK_SUCCESS ||
        !(eo.externalMemoryProperties.externalMemoryFeatures &
          VK_EXTERNAL_MEMORY_FEATURE_IMPORTABLE_BIT) ||
        !(eo.externalMemoryProperties.compatibleHandleTypes & ei.handleType) ||
        c.width > io.imageFormatProperties.maxExtent.width ||
        c.height > io.imageFormatProperties.maxExtent.height)
      return Error("RGBA8 D3D12 resource import is unsupported for this extent.");
    VkSemaphoreTypeCreateInfo st{VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO};
    st.semaphoreType = VK_SEMAPHORE_TYPE_TIMELINE;
    VkPhysicalDeviceExternalSemaphoreInfo si{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_SEMAPHORE_INFO};
    si.pNext = &st; si.handleType = VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_D3D12_FENCE_BIT;
    VkExternalSemaphoreProperties so{VK_STRUCTURE_TYPE_EXTERNAL_SEMAPHORE_PROPERTIES};
    sem_props(c.physical_device, &si, &so);
    if (!(so.externalSemaphoreFeatures & VK_EXTERNAL_SEMAPHORE_FEATURE_IMPORTABLE_BIT) ||
        !(so.compatibleHandleTypes & si.handleType))
      return Error("D3D12 fence timeline import is unsupported.");

    dxgi_ = LoadLibraryExW(L"dxgi.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    d3d12_ = LoadLibraryExW(L"d3d12.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!dxgi_ || !d3d12_) return Error("System DXGI/D3D12 unavailable.");
    fn_.pCreateFactory = reinterpret_cast<PFN_CREATE_DXGIFACTORY2>(GetProcAddress(dxgi_, "CreateDXGIFactory2"));
    fn_.pCreateDevice = reinterpret_cast<PFN_D3D12_CREATE_DEVICE>(GetProcAddress(d3d12_, "D3D12CreateDevice"));
    fn_.pGetDebugInterface = reinterpret_cast<PFN_D3D12_GET_DEBUG_INTERFACE>(GetProcAddress(d3d12_, "D3D12GetDebugInterface"));
    if (!fn_.pCreateFactory || !fn_.pCreateDevice) return Error("System DXGI exports missing.");
#define LOAD_DEVICE(name) \
    fn_.name = reinterpret_cast<PFN_##name>(c.get_device_proc(c.device, #name)); \
    if (!fn_.name) return Error("Missing " #name);
    LOAD_DEVICE(vkCreateImage)
    LOAD_DEVICE(vkGetMemoryWin32HandlePropertiesKHR)
    LOAD_DEVICE(vkGetImageMemoryRequirements)
    LOAD_DEVICE(vkAllocateMemory)
    LOAD_DEVICE(vkBindImageMemory)
    LOAD_DEVICE(vkCreateSemaphore)
    LOAD_DEVICE(vkImportSemaphoreWin32HandleKHR)
    LOAD_DEVICE(vkDestroyImage)
    LOAD_DEVICE(vkFreeMemory)
    LOAD_DEVICE(vkDestroySemaphore)
    LOAD_DEVICE(vkDeviceWaitIdle)
#undef LOAD_DEVICE
    fn_.vkGetPhysicalDeviceMemoryProperties = reinterpret_cast<PFN_vkGetPhysicalDeviceMemoryProperties>(
        c.get_instance_proc(c.instance, "vkGetPhysicalDeviceMemoryProperties"));
    submit_ = reinterpret_cast<PFN_vkQueueSubmit>(c.get_device_proc(c.device, "vkQueueSubmit"));
    if (!fn_.vkGetPhysicalDeviceMemoryProperties || !submit_)
      return Error("Required memory/queue functions missing.");
    dvk_createDeviceParameters_t dp{}; dp.pFunctions = &fn_;
    static_assert(sizeof(dp.deviceLuid) == VK_LUID_SIZE);
    std::memcpy(&dp.deviceLuid, id.deviceLUID, VK_LUID_SIZE);
    // Upstream cleans partially constructed contexts itself. Do not free twice.
    if (!Check(dvk_createDevice(dp, &dx_))) { dx_ = {}; return false; }
    device_ready_ = true;
    vk_.physicalDevice = c.physical_device; vk_.device = c.device;
    allocator_.allocate = [](size_t size, size_t alignment, void*) -> void* {
      return _aligned_malloc(size, std::max(alignment, sizeof(void*)));
    };
    allocator_.free = [](void* ptr, void*) { _aligned_free(ptr); };
    dvk_createSwapChainParameters_t sp{};
    sp.pFunctions = &fn_; sp.pAllocator = &allocator_;
    sp.pDeviceContext = &dx_; sp.pVulkanContext = &vk_;
    sp.window = c.window; sp.width = static_cast<uint16_t>(c.width);
    sp.height = static_cast<uint16_t>(c.height);
    sp.imageCount = 3; sp.maximumLatency = 2; sp.syncInterval = 1;
    // Render to an ordinary shared image. Only D3D12 accesses DXGI backbuffers.
    // The next Vulkan frame waits for the prior D3D12 copy, not only for its
    // own prior Vulkan render. Keep syncInterval=1 and the same resolution.
    sp.flags = DVK_SWAPCHAIN_BACKBUFFER_BLIT_FLAG;
    if (!Check(dvk_createSwapChain(sp, &swap_))) { swap_ = {}; return false; }
    swap_ready_ = true;
    return true;
  }
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
    if (pending_.blitValue <= pending_.submitValue || !swap_.vkBlitImage) {
      contract_.Fail(); Error("Invalid shared-image copy timeline."); return OCB_ERROR;
    }
    auto image = swap_.vkBlitImage;
    *out = {image, pending_.imageIndex, pending_.submitValue,
        ocb::display::AcquireBarrier(image, c_.queue_family, shared_image_initialized_),
        ocb::display::ReleaseBarrier(image, c_.queue_family)};
    return OCB_OK;
  }
  int Submit(const OcbDisplayFrame* frame, VkCommandBuffer cmd, VkFence fence) {
    if (!frame || !cmd || contract_.state() != FrameState::Acquired ||
        frame->image_index != pending_.imageIndex ||
        frame->signal_value != pending_.submitValue ||
        frame->image != swap_.vkBlitImage) {
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
        frame->image == swap_.vkBlitImage;
  }
  int GetImages(VkImage* images, uint32_t capacity) {
    if (!images || capacity < 3 || !swap_ready_) return OCB_ERROR;
    for (uint32_t i=0; i<3; ++i) images[i] = swap_.vkBlitImage;
    return OCB_OK;
  }
  int GetSync(const OcbDisplayFrame* frame, VkSemaphore* semaphore,
              uint64_t* wait_value, uint64_t* signal_value) {
    if (!ValidFrame(frame) || !semaphore || !wait_value || !signal_value) {
      Error("Invalid synchronization request."); return OCB_ERROR;
    }
    *semaphore = pending_.waitSemaphore;
    *wait_value = pending_.waitValue; *signal_value = pending_.submitValue;
    return OCB_OK;
  }
  int PresentSubmitted(const OcbDisplayFrame* frame) {
    if (!ValidFrame(frame)) {
      Error("Stale submitted frame."); return OCB_ERROR;
    }
    contract_.Submit(frame->image_index);
    shared_image_initialized_ = true;
    dvk_presentParameters_t p{};
    p.pSwapChain = pending_.pSwapChain; p.pCommandQueue = pending_.pCommandQueue;
    p.pCommandList = pending_.pCommandList; p.pFrameResources = pending_.pFrameResources;
    p.pFence = pending_.pFence; p.submitValue = pending_.submitValue;
    p.blitValue = pending_.blitValue; p.syncInterval = 1; p.allowTearing = false;
    if (!Check(dvk_presentImage(p))) { contract_.Fail(); return OCB_ERROR; }
    contract_.Presented(); return OCB_OK;
  }
  int Cancel() {
    if (!contract_.Cancel()) { Error("Only an unsubmitted frame can be cancelled."); return OCB_ERROR; }
    // No submission has happened. Both reserved render/copy values must be
    // discarded; the next acquire may wait only on the last real copy signal.
    swap_.fenceValue = pending_.waitValue;
    return OCB_OK;
  }
  const char* error() const { return error_; }
 private:
  OcbDisplayConfig c_{};
  HMODULE dxgi_ = nullptr, d3d12_ = nullptr;
  dvk_functions_t fn_{};
  dvk_allocator_t allocator_{};
  dvk_vulkanContext_t vk_{};
  dvk_dxgiDeviceContext_t dx_{};
  dvk_dxgiSwapChain_t swap_{};
  dvk_presentationInfo_t pending_{};
  PFN_vkQueueSubmit submit_ = nullptr;
  bool device_ready_ = false, swap_ready_ = false;
  bool shared_image_initialized_ = false;
  FrameContract contract_;
  char error_[256]{};
};
}

extern "C" void* OcbDisplayCreate(const OcbDisplayConfig* config, char* error, uint32_t capacity) {
  Bridge* b = nullptr;
  try {
    b = new Bridge;
    if (config && b->Initialize(*config)) return b;
    if (error && capacity) std::snprintf(error, capacity, "%s", config ? b->error() : "Null context.");
  } catch (...) {
    if (error && capacity) std::snprintf(error, capacity, "Bridge initialization allocation failed.");
  }
  delete b; return nullptr;
}
extern "C" int OcbDisplayAcquire(void* p, OcbDisplayFrame* f, uint32_t timeout) {
  return p ? static_cast<Bridge*>(p)->Acquire(f, timeout) : OCB_ERROR;
}
extern "C" int OcbDisplaySubmitAndPresent(void* p, const OcbDisplayFrame* f, VkCommandBuffer cmd, VkFence fence) {
  return p ? static_cast<Bridge*>(p)->Submit(f, cmd, fence) : OCB_ERROR;
}
extern "C" int OcbDisplayCancel(void* p) {
  return p ? static_cast<Bridge*>(p)->Cancel() : OCB_ERROR;
}
extern "C" int OcbDisplayGetImages(void* p, VkImage* images, uint32_t capacity) {
  return p ? static_cast<Bridge*>(p)->GetImages(images, capacity) : OCB_ERROR;
}
extern "C" int OcbDisplayGetSync(void* p, const OcbDisplayFrame* f,
    VkSemaphore* s, uint64_t* w, uint64_t* v) {
  return p ? static_cast<Bridge*>(p)->GetSync(f, s, w, v) : OCB_ERROR;
}
extern "C" int OcbDisplayPresentSubmitted(void* p, const OcbDisplayFrame* f) {
  return p ? static_cast<Bridge*>(p)->PresentSubmitted(f) : OCB_ERROR;
}
extern "C" const char* OcbDisplayLastError(void* p) {
  return p ? static_cast<Bridge*>(p)->error() : "Null display handle.";
}
extern "C" void OcbDisplayDestroy(void* p) { delete static_cast<Bridge*>(p); }
