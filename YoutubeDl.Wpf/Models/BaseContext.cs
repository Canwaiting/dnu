using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace YoutubeDl.Wpf.Models
{
    public class BaseContext : DbContext
    {
        public DbSet<SubscribeChannel> SubscribeChannels { get; set; }
        public DbSet<Video> Videos { get; set; }
        public string DbPath { get; }

        public BaseContext()
        {
            DbPath = System.IO.Path.Combine(Directory.GetCurrentDirectory(), "dnu.db");
        }

        protected override void OnConfiguring(DbContextOptionsBuilder options)
            => options.UseSqlite($"Data Source={DbPath}");
    }
}
