using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace YoutubeDl.Wpf.Models
{
    public class Video
    {
        public int Id { get; set; }
        public string Title { get; set; }
        public string Url { get; set; }

        /// <summary>
        /// 原作者上传时间，注意：统一取UTC时间
        /// </summary>
        public DateTime UploadDate { get; set; }
    }
}
