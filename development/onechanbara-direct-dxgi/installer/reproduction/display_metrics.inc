namespace {
// CPU-side presentation timings, not GPU execution time.
// Aggregate at most once a second per painting thread to avoid log I/O stalls.
class OcbDisplayStageTimer {
 public:
  explicit OcbDisplayStageTimer(bool active, bool ui_thread = false)
      : active_(active), ui_thread_(ui_thread), began_(Clock::now()),
        frame_began_(began_) {}
  ~OcbDisplayStageTimer() {
    if (!active_) return;
    FinishStage();
    const auto now = Clock::now();
    static thread_local Statistics stats;
    if (!stats.attempts) stats.began = frame_began_;
    ++stats.attempts;
    stats.presented += presented_ ? 1 : 0;
    const double frame_ms = Milliseconds(now - frame_began_);
    stats.total += frame_ms;
    stats.maximum = std::max(stats.maximum, frame_ms);
    for (size_t i = 0; i < times_.size(); ++i) {
      stats.stages[i] += times_[i];
      stats.max_stages[i] = std::max(stats.max_stages[i], times_[i]);
    }
    const double elapsed = Milliseconds(now - stats.began);
    if (elapsed >= 1000.0) {
      const double count = double(stats.attempts);
      XELOGI("Onechanbara display stats: thread={} period_ms={:.1f} "
             "attempts={} presented={} cpu_avg_ms={:.2f} cpu_max_ms={:.2f} "
             "completion_avg_max={:.2f}/{:.2f} prepare_avg_max={:.2f}/{:.2f} "
             "acquire_avg_max={:.2f}/{:.2f} record_avg_max={:.2f}/{:.2f} "
             "submit_avg_max={:.2f}/{:.2f} present_avg_max={:.2f}/{:.2f}",
             ui_thread_ ? "UI" : "guest-output", elapsed,
             stats.attempts, stats.presented, stats.total / count, stats.maximum,
             stats.stages[0] / count, stats.max_stages[0],
             stats.stages[1] / count, stats.max_stages[1],
             stats.stages[2] / count, stats.max_stages[2],
             stats.stages[3] / count, stats.max_stages[3],
             stats.stages[4] / count, stats.max_stages[4],
             stats.stages[5] / count, stats.max_stages[5]);
      stats = Statistics{};
    }
  }
  void Stage(const char*) {
    if (!active_) return;
    FinishStage();
    if (stage_ + 1 < times_.size()) ++stage_;
    began_ = Clock::now();
  }
  void Presented() { presented_ = true; }
 private:
  using Clock = std::chrono::steady_clock;
  struct Statistics {
    Clock::time_point began{};
    uint64_t attempts = 0, presented = 0;
    double total = 0, maximum = 0;
    std::array<double, 6> stages{}, max_stages{};
  };
  static double Milliseconds(Clock::duration duration) {
    return std::chrono::duration<double, std::milli>(duration).count();
  }
  void FinishStage() {
    times_[stage_] += Milliseconds(Clock::now() - began_);
  }
  bool active_, ui_thread_, presented_ = false;
  size_t stage_ = 0;
  std::array<double, 6> times_{};
  Clock::time_point began_, frame_began_;
};
}  // namespace
