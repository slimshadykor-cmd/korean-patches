using System; class StandaloneCli {static int Main(string[] a){try{Standalone.Apply(a[0],a[1],Console.WriteLine);return 0;}catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}}}
