using System;
using System.ComponentModel.DataAnnotations.Schema;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Data;

namespace YoutubeDl.Wpf.Models
{
    public class Video
    {
        public int Id { get; set; }
        public string Title { get; set; }
        public string Url { get; set; }
        public DateTime UploadDate { get; set; } //原作者上传时间，注意：统一取UTC时间后转换成中国标准时间
        public bool? IsDownload { get; set; } = false;
        public bool? IsUpload { get; set; } = false; //加上?，就可以使得即使数据库中的为空，也不用报错了
        public string? ChannelId { get; set; } = "";
        
        public Video()
        {
        }

        public Video(YoutubeExplode.Videos.Video video)
        {
            Title = video.Title;
            Url = video.Url;
            UploadDate = DateTimeExtensions.ConvertToChinaStandardTime(video.UploadDate.UtcDateTime);
            IsDownload = false;
            IsUpload = false;
            ChannelId = video.Author.ChannelId;
        }
    }

    #region 转换器
    public class IsDownloadConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            if (value != null && (bool)value == true)
            {
                return "已下载";
            }
            return "未下载";
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    public class IsUploadConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            if (value != null && (bool)value == true)
            {
                return "已上传";
            }
            return "未上传";
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
    #endregion

}
