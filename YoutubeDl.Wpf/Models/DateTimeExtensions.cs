using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace YoutubeDl.Wpf.Models
{
    public static class DateTimeExtensions
    {
        public static DateTime RoundDown(this DateTime dt, TimeSpan d)
        {
            var delta = dt.Ticks % d.Ticks;
            return new DateTime(dt.Ticks - delta, dt.Kind);
        }

        /// <summary>
        /// 转换成中国标准时间（YYYY-MM-DD HH:MM:SS）
        /// </summary>
        /// <returns></returns>
        public static DateTime ConvertToChinaStandardTime(DateTime input)
        {
            TimeZoneInfo chinaZone = TimeZoneInfo.FindSystemTimeZoneById("China Standard Time");
            DateTime output = TimeZoneInfo.ConvertTimeFromUtc(input.ToUniversalTime(), chinaZone);
            output = new DateTime(output.Year, output.Month, output.Day, output.Hour, output.Minute, output.Second);
            return output;
        }
    }

}
