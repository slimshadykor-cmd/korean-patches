using System;
using System.IO;
using System.Web.Script.Serialization;
class FakeRuntime {
 static int Main(string[] args) {
  File.WriteAllText("probe-args.json",new JavaScriptSerializer().Serialize(args));
  Console.WriteLine("MOCK_RUNTIME_STARTED");
  Console.Error.WriteLine("MOCK_STDERR_CAPTURED");
  return 0;
 }
}
