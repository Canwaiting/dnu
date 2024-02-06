using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace YoutubeDl.Wpf.Models
{
    public class SubscribeChannel
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string ChannelId { get; set; }
        public DateTime SubscribeDate { get; set; }
        public DateTime? LastPullLatestDate { get; set; } //上一次拉取最新的时间
    }
}
