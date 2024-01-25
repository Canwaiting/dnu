using Serilog;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace YoutubeDl.Wpf.Models
{
    public class LoggerService
    {
        private Dictionary<string, ILogger> _loggers = new Dictionary<string, ILogger>();

        public void AddLogger(string name, ILogger logger)
        {
            _loggers[name] = logger;
        }

        public ILogger GetLogger(string name)
        {
            return _loggers.TryGetValue(name, out var logger) ? logger : null;
        }
    }

}
