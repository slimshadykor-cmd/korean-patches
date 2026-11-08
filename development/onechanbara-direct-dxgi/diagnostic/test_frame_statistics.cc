#include "generator/non_nv/integration/diagnostic_statistics.h"
#include <cassert>
#include <iostream>
int main() {
  OcbDisplayStatistics s;
  s.generation = 3;
  s.RecordFrame(10, 2);
  s.RecordFrame(10, 4);  // Window repaint is a repeat, not a dropped frame.
  s.RecordFrame(13, 6);  // Guest frames 11,12 did not reach a successful API call.
  assert(s.id_duplicates==1 && s.id_gaps==2 && s.id_max_gap==2);
  assert(s.id_first==10 && s.id_last==13 && s.age_total_ms==12);
  s.NewWindow();
  assert(s.generation==3 && s.id_previous==13 && s.frame_samples==0);
  s.RecordFrame(16, 8);
  assert(s.id_gaps==2 && s.id_first==16 && s.id_last==16);
  s.RecordFrame(15, 10); // Detect without unsigned-underflow false giant gap.
  assert(s.id_regressions==1 && s.id_gaps==2);
  s.RecordFrame(0, 100); // Inactive guest images don't become 'lost' frames.
  assert(s.frame_samples==2);
  s={};s.generation=4;s.RecordFrame(500,1); // Reconnect starts a fresh sequence.
  assert(s.id_gaps==0 && s.id_duplicates==0);
  std::cout << "frame-statistics: passed\n";
}
