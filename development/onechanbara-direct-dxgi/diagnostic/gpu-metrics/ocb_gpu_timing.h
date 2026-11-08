// Diagnostic-only GPU timestamp interval for the final Vulkan presentation pass.
// This interval can include semaphore stalls and other queue overlap. It is NOT
// engine-busy time, Xbox 360 frame render time, or a scanout metric.
#ifndef XENIA_UI_VULKAN_OCB_GPU_TIMING_H_
#define XENIA_UI_VULKAN_OCB_GPU_TIMING_H_

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <vector>

#include <vulkan/vulkan.h>
#include "xenia/base/logging.h"

class OcbVulkanOutputGpuTiming {
 public:
  struct Context {
    VkDevice device;
    VkPhysicalDevice physical_device;
    uint32_t queue_family;
    PFN_vkGetDeviceProcAddr get_device_proc;
    PFN_vkGetPhysicalDeviceProperties get_properties;
    PFN_vkGetPhysicalDeviceQueueFamilyProperties get_families;
  };

  // Call under the presenter's existing paint lock, after its normal completion
  // update. A full diagnostic ring skips this sample; it never waits.
  int Begin(bool enabled, const Context& context, VkCommandBuffer command_buffer,
            uint64_t submission, uint64_t completed_submission) {
    if (!enabled) return -1;
    if (!initialized_) Initialize(context);
    if (!pool_) return -1;
    Collect(completed_submission);
    const uint32_t slot = uint32_t(submission % kSlotCount);
    if (slots_[slot].pending) {
      ++skipped_;
      Flush(false);
      return -1;
    }
    // Command reset is ordered before both writes, needs no hostQueryReset.
    reset_query_(command_buffer, pool_, slot * 2, 2);
    // TOP->BOTTOM measures the output command interval, including semaphore
    // stalls. No added barrier serializes the GPU merely for measurement.
    write_timestamp_(command_buffer, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                     pool_, slot * 2);
    slots_[slot].submission = submission;
    slots_[slot].ended = false;
    return int(slot);
  }

  void End(int slot, VkCommandBuffer command_buffer) {
    if (slot < 0) return;
    write_timestamp_(command_buffer, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
                     pool_, uint32_t(slot) * 2 + 1);
    slots_[slot].ended = true;
  }

  // Only mark a sample live after the normal queue submission succeeded.
  // An early-return or failed submission can be reset on the next attempt.
  void Submitted(int slot) {
    if (slot >= 0 && slots_[slot].ended) slots_[slot].pending = true;
  }

  // Caller has already performed its normal swapchain retirement wait.
  // This method must never introduce a new queue/device wait.
  void DestroyAfterIdle() {
    if (pool_) {
      Collect(UINT64_MAX);
      Flush(true);
      destroy_query_(context_.device, pool_, nullptr);
    }
    pool_ = VK_NULL_HANDLE;
    initialized_ = false;
    for (auto& slot : slots_) slot = Slot{};
    samples_ = skipped_ = unavailable_ = errors_ = 0;
    total_ms_ = maximum_ms_ = 0;
    first_submission_ = last_submission_ = 0;
  }

  static uint64_t TickDelta(uint64_t start, uint64_t end, uint32_t valid_bits) {
    const uint64_t mask = valid_bits >= 64 ? UINT64_MAX
        : (uint64_t(1) << valid_bits) - 1;
    return (end - start) & mask;
  }

 private:
  using Clock = std::chrono::steady_clock;
  static constexpr uint32_t kSlotCount = 8;
  struct Slot {
    uint64_t submission = 0;
    bool pending = false;
    bool ended = false;
  };
  void Initialize(const Context& context) {
    initialized_ = true;
    context_ = context;
    began_ = Clock::now();
    if (!context.device || !context.physical_device ||
        !context.get_device_proc || !context.get_properties ||
        !context.get_families) {
      XELOGI("Onechanbara GPU output probe: unavailable missing API context");
      return;
    }
    uint32_t count = 0;
    context.get_families(context.physical_device, &count, nullptr);
    std::vector<VkQueueFamilyProperties> families(count);
    context.get_families(context.physical_device, &count, families.data());
    VkPhysicalDeviceProperties properties{};
    context.get_properties(context.physical_device, &properties);
    if (context.queue_family >= count) return;
    valid_bits_ = families[context.queue_family].timestampValidBits;
    timestamp_period_ = properties.limits.timestampPeriod;
    if (!valid_bits_ || valid_bits_ > 64 ||
        !(timestamp_period_ > 0) || !std::isfinite(timestamp_period_)) {
      XELOGI("Onechanbara GPU output probe: unavailable timestamp support");
      return;
    }
#define OCB_LOAD_QUERY(member, name) \
    member = reinterpret_cast<PFN_##name>( \
        context.get_device_proc(context.device, #name));
    OCB_LOAD_QUERY(create_query_, vkCreateQueryPool)
    OCB_LOAD_QUERY(destroy_query_, vkDestroyQueryPool)
    OCB_LOAD_QUERY(reset_query_, vkCmdResetQueryPool)
    OCB_LOAD_QUERY(write_timestamp_, vkCmdWriteTimestamp)
    OCB_LOAD_QUERY(get_results_, vkGetQueryPoolResults)
#undef OCB_LOAD_QUERY
    if (!create_query_ || !destroy_query_ || !reset_query_ ||
        !write_timestamp_ || !get_results_) {
      XELOGI("Onechanbara GPU output probe: unavailable query functions");
      return;
    }
    VkQueryPoolCreateInfo info{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};
    info.queryType = VK_QUERY_TYPE_TIMESTAMP;
    info.queryCount = kSlotCount * 2;
    if (create_query_(context.device, &info, nullptr, &pool_) != VK_SUCCESS) {
      pool_ = VK_NULL_HANDLE;
      XELOGI("Onechanbara GPU output probe: unavailable query allocation");
      return;
    }
    XELOGI("Onechanbara GPU output probe: enabled scope=final-output-interval "
           "timestamp_bits={} timestamp_period_ns={} ring={} no-extra-waits "
           "includes-semaphore-stalls=true engine-busy=false",
           valid_bits_, timestamp_period_, kSlotCount);
  }

  void Collect(uint64_t completed_submission) {
    for (uint32_t i = 0; i < kSlotCount; ++i) {
      auto& slot = slots_[i];
      if (!slot.pending || slot.submission > completed_submission) continue;
      // Timestamp and availability are both 64-bit. No WAIT_BIT, no PARTIAL.
      uint64_t results[4]{};
      const VkResult result = get_results_(context_.device, pool_, i * 2, 2,
          sizeof(results), results, sizeof(uint64_t) * 2,
          VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT);
      if (result == VK_NOT_READY ||
          (result == VK_SUCCESS && (!results[1] || !results[3]))) {
        ++unavailable_;
        continue;
      }
      slot.pending = false;
      if (result != VK_SUCCESS) {
        ++errors_;
        continue;
      }
      const double ms = double(TickDelta(results[0], results[2], valid_bits_)) *
          timestamp_period_ / 1000000.0;
      // A timestamp counter with N bits wraps every 2^N * period nanoseconds.
      // Unwrapping more than one full counter period is impossible from a pair;
      // timestamp_bits and period are logged so analysts can reject that case.
      total_ms_ += ms;
      maximum_ms_ = std::max(maximum_ms_, ms);
      if (!samples_) first_submission_ = last_submission_ = slot.submission;
      first_submission_ = std::min(first_submission_, slot.submission);
      last_submission_ = std::max(last_submission_, slot.submission);
      ++samples_;
    }
    Flush(false);
  }

  void Flush(bool force) {
    const auto now = Clock::now();
    const double elapsed = std::chrono::duration<double, std::milli>(now - began_).count();
    if ((!force && elapsed < 1000) || !(samples_ || skipped_ || unavailable_ || errors_)) return;
    XELOGI("Onechanbara GPU output stats: period_ms={:.1f} samples={} "
           "gpu_output_interval_avg_ms={:.4f} gpu_output_interval_max_ms={:.4f} "
           "min_submission={} max_submission={} skipped={} unavailable={} "
           "query_errors={} scope=final-output-interval scanout=false "
           "guest-render=false engine-busy=false includes-semaphore-stalls=true",
           elapsed, samples_, samples_ ? total_ms_ / double(samples_) : 0.0,
           maximum_ms_, first_submission_, last_submission_, skipped_,
           unavailable_, errors_);
    began_ = now;
    samples_ = skipped_ = unavailable_ = errors_ = 0;
    total_ms_ = maximum_ms_ = 0;
    first_submission_ = last_submission_ = 0;
  }

  bool initialized_ = false;
  Context context_{};
  VkQueryPool pool_ = VK_NULL_HANDLE;
  uint32_t valid_bits_ = 0;
  double timestamp_period_ = 0;
  std::array<Slot, kSlotCount> slots_{};
  PFN_vkCreateQueryPool create_query_ = nullptr;
  PFN_vkDestroyQueryPool destroy_query_ = nullptr;
  PFN_vkCmdResetQueryPool reset_query_ = nullptr;
  PFN_vkCmdWriteTimestamp write_timestamp_ = nullptr;
  PFN_vkGetQueryPoolResults get_results_ = nullptr;
  Clock::time_point began_{};
  uint64_t samples_ = 0, skipped_ = 0, unavailable_ = 0, errors_ = 0;
  uint64_t first_submission_ = 0, last_submission_ = 0;
  double total_ms_ = 0, maximum_ms_ = 0;
};

#endif  // XENIA_UI_VULKAN_OCB_GPU_TIMING_H_
