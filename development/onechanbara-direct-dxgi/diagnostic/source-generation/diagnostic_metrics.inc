namespace {
class OcbDisplayStageTimer {
 public:
  using Clock = std::chrono::steady_clock;
  OcbDisplayStageTimer(OcbDisplayStatistics& stats, bool active,
                      bool ui_thread, bool direct)
      : stats_(stats), active_(active), ui_thread_(ui_thread), direct_(direct) {
    if (active_) began_ = frame_began_ = Clock::now();
  }
  ~OcbDisplayStageTimer() {
    if (!active_) return;
    FinishStage();
    const auto now = Clock::now();
    if (!stats_.attempts) stats_.began = frame_began_;
    ++stats_.attempts;
    stats_.ui_attempts += ui_thread_;
    stats_.presented += presented_;
    const double frame_ms = Milliseconds(now - frame_began_);
    stats_.total += frame_ms;
    stats_.maximum = std::max(stats_.maximum, frame_ms);
    for (size_t i = 0; i < times_.size(); ++i) {
      stats_.stages[i] += times_[i];
      stats_.max_stages[i] = std::max(stats_.max_stages[i], times_[i]);
    }
    if (presented_ && id_) {
      const auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
          now.time_since_epoch()).count();
      stats_.RecordFrame(id_, ns >= publish_ns_ ? double(ns-publish_ns_)/1.0e6 : 0.0);
    }
    const double elapsed = Milliseconds(now-stats_.began);
    if (elapsed < 1000.0) return;
    const double n = double(stats_.attempts);
    const double a = double(std::max<uint64_t>(1, stats_.acquire_calls));
    const double f = double(std::max<uint64_t>(1, stats_.frame_samples));
    XELOGI("Onechanbara diagnostic CPU: path={} generation={} steady_ns={} period_ms={:.1f} "
           "attempts={} present_api_ok={} ui_calls={} guest_calls={} "
           "cpu_avg_max={:.3f}/{:.3f} completion_avg_max={:.3f}/{:.3f} "
           "prepare_avg_max={:.3f}/{:.3f} acquire_avg_max={:.3f}/{:.3f} "
           "record_avg_max={:.3f}/{:.3f} submit_avg_max={:.3f}/{:.3f} "
           "present_avg_max={:.3f}/{:.3f} latency_wait_avg_max={:.3f}/{:.3f} "
           "allocator_wait_avg_max={:.3f}/{:.3f} acquire_calls={} acquire_timeouts={} acquire_errors={} "
           "consumed_calls={} submitted={} allocated_latest_id={} consumed_latest_id={} "
           "id_first={} id_last={} id_gaps={} id_max_gap={} duplicates={} regressions={} "
           "publish_to_api_avg_max_ms={:.3f}/{:.3f}",
           direct_ ? "direct" : "native", stats_.generation,
           std::chrono::duration_cast<std::chrono::nanoseconds>(now.time_since_epoch()).count(),
           elapsed,stats_.attempts,stats_.presented,stats_.ui_attempts,
           stats_.attempts-stats_.ui_attempts,stats_.total/n,stats_.maximum,
           stats_.stages[0]/n,stats_.max_stages[0],stats_.stages[1]/n,stats_.max_stages[1],
           stats_.stages[2]/n,stats_.max_stages[2],stats_.stages[3]/n,stats_.max_stages[3],
           stats_.stages[4]/n,stats_.max_stages[4],stats_.stages[5]/n,stats_.max_stages[5],
           stats_.latency_wait/a,stats_.latency_wait_max,
           stats_.allocator_wait/a,stats_.allocator_wait_max,
           stats_.acquire_calls,stats_.acquire_timeouts,stats_.acquire_errors,
           stats_.consumed,stats_.submitted,stats_.produced_latest,stats_.consumed_latest,
           stats_.id_first,stats_.id_last,stats_.id_gaps,stats_.id_max_gap,
           stats_.id_duplicates,stats_.id_regressions,stats_.age_total_ms/f,stats_.age_max_ms);
    stats_.NewWindow();
  }
  void Stage(size_t stage) {
    if (!active_) return;
    FinishStage();
    stage_ = stage;
    began_ = Clock::now();
  }
  void Acquired(double latency, double allocator, int result) {
    if (!active_) return;
    ++stats_.acquire_calls;
    stats_.latency_wait += latency;
    stats_.latency_wait_max = std::max(stats_.latency_wait_max,latency);
    stats_.allocator_wait += allocator;
    stats_.allocator_wait_max = std::max(stats_.allocator_wait_max,allocator);
    stats_.acquire_timeouts += result == 1;
    stats_.acquire_errors += result < 0;
  }
  void Frame(uint64_t id, int64_t publish_ns, uint64_t produced) {
    if (!active_) return;
    id_ = id; publish_ns_ = publish_ns;
    ++stats_.consumed; stats_.produced_latest = produced; stats_.consumed_latest = id;
  }
  void Submitted() { if (active_) ++stats_.submitted; }
  void Presented() { presented_ = true; }
 private:
  static double Milliseconds(Clock::duration t) {
    return std::chrono::duration<double,std::milli>(t).count();
  }
  void FinishStage() { times_[stage_] += Milliseconds(Clock::now()-began_); }
  OcbDisplayStatistics& stats_;
  bool active_, ui_thread_, direct_, presented_ = false;
  size_t stage_ = 0;
  uint64_t id_ = 0;
  int64_t publish_ns_ = 0;
  std::array<double,6> times_{};
  Clock::time_point began_{}, frame_began_{};
};
}  // namespace
