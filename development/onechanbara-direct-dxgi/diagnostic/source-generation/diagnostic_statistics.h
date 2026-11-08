#pragma once
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>

// Owned by one presenter. Its existing painting ownership serializes access.
// These are CPU/API-delivery measurements, never monitor scanout measurements.
struct OcbDisplayStatistics {
  using Clock = std::chrono::steady_clock;
  Clock::time_point began{};
  uint64_t attempts = 0, presented = 0, ui_attempts = 0;
  uint64_t consumed = 0, submitted = 0, produced_latest = 0, consumed_latest = 0;
  double total = 0, maximum = 0;
  std::array<double, 6> stages{}, max_stages{};
  double latency_wait = 0, latency_wait_max = 0;
  double allocator_wait = 0, allocator_wait_max = 0;
  uint64_t acquire_calls = 0, acquire_timeouts = 0, acquire_errors = 0;
  uint64_t id_first = 0, id_last = 0, id_previous = 0;
  uint64_t id_gaps = 0, id_max_gap = 0, id_duplicates = 0, id_regressions = 0;
  uint64_t frame_samples = 0;
  double age_total_ms = 0, age_max_ms = 0;
  uint64_t generation = 0;
  void NewWindow() {
    const uint64_t previous = id_previous, gen = generation;
    *this = {};
    id_previous = previous;
    generation = gen;
  }
  void RecordFrame(uint64_t id, double age_ms) {
    if (!id) return;
    if (!id_first) id_first = id;
    id_last = id;
    if (id_previous) {
      if (id == id_previous) ++id_duplicates;
      else if (id < id_previous) ++id_regressions;
      else {
        const uint64_t gap = id - id_previous - 1;
        id_gaps += gap;
        id_max_gap = std::max(id_max_gap, gap);
      }
    }
    id_previous = id;
    ++frame_samples;
    age_total_ms += age_ms;
    age_max_ms = std::max(age_max_ms, age_ms);
  }
};
