#include <cassert>
#include <cstdio>
#include <cstring>
#include "ocb_gpu_timing.h"

namespace {
unsigned creates, destroys, resets, writes, reads, last_query;
uint32_t bits = 64;
bool allocation_fails = false, available = true;
VkResult read_result = VK_SUCCESS;
VkResult VKAPI_PTR Create(VkDevice, const VkQueryPoolCreateInfo* info,
    const VkAllocationCallbacks*, VkQueryPool* pool) {
  ++creates; assert(info->queryType == VK_QUERY_TYPE_TIMESTAMP);
  assert(info->queryCount == 16);
  if (allocation_fails) return VK_ERROR_OUT_OF_DEVICE_MEMORY;
  *pool = reinterpret_cast<VkQueryPool>(uintptr_t(42)); return VK_SUCCESS;
}
void VKAPI_PTR Destroy(VkDevice, VkQueryPool, const VkAllocationCallbacks*) { ++destroys; }
void VKAPI_PTR Reset(VkCommandBuffer, VkQueryPool, uint32_t first, uint32_t count) {
  ++resets; assert(first < 16 && !(first % 2) && count == 2);
}
void VKAPI_PTR Write(VkCommandBuffer, VkPipelineStageFlagBits stage,
                    VkQueryPool, uint32_t query) {
  ++writes; assert(stage == ((query % 2) ? VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT :
                                          VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT));
  assert(query < 16);
}
VkResult VKAPI_PTR Read(VkDevice, VkQueryPool, uint32_t first, uint32_t count,
                       size_t size, void* output, VkDeviceSize stride,
                       VkQueryResultFlags flags) {
  ++reads; last_query = first;
  assert(count == 2 && size == 32 && stride == 16);
  assert(flags == (VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT));
  uint64_t values[] = {100, uint64_t(available), 1100, uint64_t(available)};
  std::memcpy(output, values, sizeof(values)); return read_result;
}
PFN_vkVoidFunction VKAPI_PTR Get(VkDevice, const char* name) {
  if (!std::strcmp(name, "vkCreateQueryPool")) return reinterpret_cast<PFN_vkVoidFunction>(Create);
  if (!std::strcmp(name, "vkDestroyQueryPool")) return reinterpret_cast<PFN_vkVoidFunction>(Destroy);
  if (!std::strcmp(name, "vkCmdResetQueryPool")) return reinterpret_cast<PFN_vkVoidFunction>(Reset);
  if (!std::strcmp(name, "vkCmdWriteTimestamp")) return reinterpret_cast<PFN_vkVoidFunction>(Write);
  if (!std::strcmp(name, "vkGetQueryPoolResults")) return reinterpret_cast<PFN_vkVoidFunction>(Read);
  assert(false); return nullptr;
}
void VKAPI_PTR Properties(VkPhysicalDevice, VkPhysicalDeviceProperties* p) {
  p->limits.timestampPeriod = 1.0f;
}
void VKAPI_PTR Families(VkPhysicalDevice, uint32_t* n, VkQueueFamilyProperties* p) {
  *n = 1; if (p) { p->timestampValidBits = bits; p->queueFlags = VK_QUEUE_GRAPHICS_BIT; }
}
void Clear() { creates=destroys=resets=writes=reads=last_query=0; bits=64;
  allocation_fails=false; available=true; read_result=VK_SUCCESS; }
}
int main() {
  OcbVulkanOutputGpuTiming::Context context{
      reinterpret_cast<VkDevice>(uintptr_t(1)), reinterpret_cast<VkPhysicalDevice>(uintptr_t(2)),
      0, Get, Properties, Families};
  auto cmd = reinterpret_cast<VkCommandBuffer>(uintptr_t(3));
  assert(OcbVulkanOutputGpuTiming::TickDelta(250, 7, 8) == 13);
  assert(OcbVulkanOutputGpuTiming::TickDelta(UINT64_MAX-9, 10, 64) == 20);
  assert(OcbVulkanOutputGpuTiming::TickDelta(100, 1100, 36) == 1000);
  {
    Clear(); OcbVulkanOutputGpuTiming timing;
    assert(timing.Begin(false, context, cmd, 1, 0) == -1);
    assert(creates == 0 && writes == 0 && reads == 0);
    timing.DestroyAfterIdle(); assert(destroys == 0);
  }
  {
    Clear(); bits=0; OcbVulkanOutputGpuTiming timing;
    assert(timing.Begin(true, context, cmd, 1, 0) == -1);
    assert(creates == 0); timing.DestroyAfterIdle();
  }
  {
    Clear(); allocation_fails=true; OcbVulkanOutputGpuTiming timing;
    assert(timing.Begin(true, context, cmd, 1, 0) == -1);
    assert(timing.Begin(true, context, cmd, 2, 0) == -1);
    assert(creates == 1 && resets == 0); timing.DestroyAfterIdle();
  }
  {
    Clear(); OcbVulkanOutputGpuTiming timing;
    int a=timing.Begin(true, context, cmd, 1, 0);
    timing.End(a,cmd); timing.Submitted(a);
    int b=timing.Begin(true, context, cmd, 2, 0);
    assert(b >= 0 && reads == 0); // Previous query availability is never trusted without fence.
    int c=timing.Begin(true, context, cmd, 3, 1);
    assert(c >= 0 && reads == 1 && last_query == 2);
    // Unsubmitted commands do not become pending and need no completion wait.
    assert(timing.Begin(true, context, cmd, 2, 1) == b);
    assert(reads == 1);
    timing.DestroyAfterIdle(); assert(destroys == 1);
  }
  {
    Clear(); OcbVulkanOutputGpuTiming timing;
    int a=timing.Begin(true,context,cmd,1,0); timing.End(a,cmd); timing.Submitted(a);
    read_result=VK_NOT_READY;
    assert(timing.Begin(true,context,cmd,9,1) == -1); // Full slot skipped, not waited/reset.
    assert(reads == 1 && resets == 1);
    read_result=VK_SUCCESS; available=false;
    assert(timing.Begin(true,context,cmd,9,1) == -1);
    assert(reads == 2 && resets == 1);
    available=true;
    assert(timing.Begin(true,context,cmd,9,1) == a);
    assert(reads == 3 && resets == 2);
    timing.DestroyAfterIdle();
  }
  {
    Clear(); OcbVulkanOutputGpuTiming timing;
    int a=timing.Begin(true,context,cmd,1,0); timing.Submitted(a); // End never recorded.
    assert(timing.Begin(true,context,cmd,9,0) == a);
    assert(reads == 0 && resets == 2);
    timing.End(a,cmd); timing.Submitted(a);
    read_result=VK_ERROR_DEVICE_LOST;
    assert(timing.Begin(true,context,cmd,17,9) == a);
    assert(reads == 1); timing.DestroyAfterIdle();
  }
  std::puts("GPU query protocol checks passed (mock API; no physical GPU).");
}
