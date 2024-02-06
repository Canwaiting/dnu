using System.Windows.Forms;
using System;
using System.Collections.Generic;
using System.Net;
using YoutubeExplode.Common;
using DynamicData;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using Splat;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using YoutubeDl.Wpf.Utils;
using YoutubeExplode;
using YoutubeExplode.Playlists;

namespace YoutubeDl.Wpf.Models;

public class BackendInstance : ReactiveObject, IEnableLogger
{
    // 定义一些私有变量
    private readonly ObservableSettings _settings;
    private readonly BackendService _backendService;
    private readonly Process _process;
    private readonly Process _myprocess;

    // 生成的下载参数列表
    public List<string> GeneratedDownloadArguments { get; } = new();

    // 下载进度百分比，0.99表示99%
    [Reactive]
    public double DownloadProgressPercentage { get; set; }

    // 状态是否不确定
    [Reactive]
    public bool StatusIndeterminate { get; set; }

    // 是否正在运行
    [Reactive]
    public bool IsRunning { get; set; }

    // 文件大小字符串
    [Reactive]
    public string FileSizeString { get; set; } = "";

    // 下载速度字符串
    [Reactive]
    public string DownloadSpeedString { get; set; } = "";

    // 下载预计剩余时间字符串
    [Reactive]
    public string DownloadETAString { get; set; } = "";

    // 构造函数
    public BackendInstance(ObservableSettings settings, BackendService backendService)
    {
        _settings = settings;
        _backendService = backendService;

        _process = new();
        _process.StartInfo.CreateNoWindow = true;
        _process.StartInfo.UseShellExecute = false;
        _process.StartInfo.RedirectStandardError = true;
        _process.StartInfo.RedirectStandardOutput = true;
        _process.StartInfo.StandardErrorEncoding = Encoding.UTF8;
        _process.StartInfo.StandardOutputEncoding = Encoding.UTF8;
        _process.EnableRaisingEvents = true;


        _myprocess = new();
        _myprocess.StartInfo.CreateNoWindow = true;
        _myprocess.StartInfo.UseShellExecute = false;
        _myprocess.StartInfo.RedirectStandardError = true;
        _myprocess.StartInfo.RedirectStandardOutput = true;
        _myprocess.StartInfo.StandardErrorEncoding = Encoding.UTF8;
        _myprocess.StartInfo.StandardOutputEncoding = Encoding.UTF8;
        _myprocess.EnableRaisingEvents = true;
    }

    // 异步运行方法
    private async Task RunAsync(CancellationToken cancellationToken = default, Serilog.ILogger logger = null)
    {
        if (!_process.Start())
            throw new InvalidOperationException("Method called when the backend process is running.");


        SetStatusRunning();

        await Task.WhenAll(
            ReadAndParseLinesAsync(_process.StandardError, cancellationToken, logger),
            ReadAndParseLinesAsync(_process.StandardOutput, cancellationToken, logger),
            _process.WaitForExitAsync(cancellationToken));

        SetStatusStopped();
    }

    // 异步运行方法
    private async Task RunNormalDownloadAsync(CancellationToken cancellationToken = default)
    {
        if (!_process.Start())
            throw new InvalidOperationException("Method called when the backend process is running.");

        var loggerService = Locator.Current.GetService<LoggerService>();
        var logger = loggerService.GetLogger("subscribeChannelViewLogger");

        await Task.WhenAll(
            ReadAndParseLinesAsync(_process.StandardError, cancellationToken, logger),
            ReadAndParseLinesAsync(_process.StandardOutput, cancellationToken, logger),
            _process.WaitForExitAsync(cancellationToken));
    }

    // 设置状态为运行中
    private void SetStatusRunning()
    {
        StatusIndeterminate = true;
        IsRunning = true;
        _backendService.UpdateProgress();
    }

    // 设置状态为已停止
    private void SetStatusStopped()
    {
        DownloadProgressPercentage = 0.0;
        StatusIndeterminate = false;
        IsRunning = false;
        _backendService.UpdateProgress();
    }

    // 异步读取和解析行
    private async Task ReadAndParseLinesAsync(StreamReader reader, CancellationToken cancellationToken = default, Serilog.ILogger logger = null)
    {
        while (true)
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (line == null)
            {
                return;
            }

            if (logger == null)
            {
                return;
            }

            string message = line + "\n";
            logger.Information(message);
            ParseLine(line);
        }
    }

    // 解析行
    private void ParseLine(ReadOnlySpan<char> line)
    {
        // 示例行：
        // [download]   0.0% of 36.35MiB at 20.40KiB/s ETA 30:24
        // [download]  65.1% of 36.35MiB at  2.81MiB/s ETA 00:04
        // [download] 100% of 36.35MiB in 00:10

        // 检查并去除下载前缀。
        const string downloadPrefix = "[download] ";
        if (!line.StartsWith(downloadPrefix, StringComparison.Ordinal))
            return;
        line = line[downloadPrefix.Length..];

        // 解析并去除百分比。
        const string percentageSuffix = "% of ";
        var percentageEnd = line.IndexOf(percentageSuffix, StringComparison.Ordinal);
        if (percentageEnd == -1 || !double.TryParse(line[..percentageEnd], NumberStyles.AllowLeadingWhite | NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out var percentage))
            return;
        DownloadProgressPercentage = percentage / 100;
        StatusIndeterminate = false;
        _backendService.UpdateProgress();
        line = line[(percentageEnd + percentageSuffix.Length)..];

        // 情况0：下载进行中
        const string speedPrefix = " at ";
        var sizeEnd = line.IndexOf(speedPrefix, StringComparison.Ordinal);
        if (sizeEnd != -1)
        {
            // 提取并去除文件大小。
            FileSizeString = line[..sizeEnd].ToString();
            line = line[(sizeEnd + speedPrefix.Length)..];

            // 提取并去除速度。
            const string etaPrefix = " ETA ";
            var speedEnd = line.IndexOf(etaPrefix, StringComparison.Ordinal);
            if (speedEnd == -1)
                return;
            DownloadSpeedString = line[..speedEnd].TrimStart().ToString();
            line = line[(speedEnd + etaPrefix.Length)..];

            // 提取ETA字符串。
            DownloadETAString = line.ToString();
            return;
        }

        // 情况1：下载完成
        sizeEnd = line.IndexOf(" in ", StringComparison.Ordinal);
        if (sizeEnd != -1)
        {
            // 提取文件大小。
            FileSizeString = line[..sizeEnd].ToString();
        }
    }


    // 生成下载参数
    public void GenerateDownloadArguments(string playlistItems)
    {
        GeneratedDownloadArguments.Clear();

        if (!string.IsNullOrEmpty(_settings.Proxy))
        {
            GeneratedDownloadArguments.Add("--proxy");
            GeneratedDownloadArguments.Add(_settings.Proxy);
        }

        if (!string.IsNullOrEmpty(_settings.FfmpegPath))
        {
            GeneratedDownloadArguments.Add("--ffmpeg-location");
            GeneratedDownloadArguments.Add(_settings.FfmpegPath);
        }

        if (_settings.SelectedPreset is not null)
        {
            GeneratedDownloadArguments.AddRange(_settings.SelectedPreset.ToArgs());
        }

        if (_settings.DownloadSubtitles)
        {
            if (_settings.Backend == BackendTypes.Ytdl)
            {
                GeneratedDownloadArguments.Add("--write-sub");
            }
        }

        if (_settings.DownloadSubtitlesAllLanguages)
        {
            if (_settings.Backend == BackendTypes.Ytdl)
            {
                GeneratedDownloadArguments.Add("--all-subs");
            }

            if (_settings.Backend == BackendTypes.Ytdlp)
            {
                GeneratedDownloadArguments.Add("--sub-langs");
                GeneratedDownloadArguments.Add("all");
            }
        }

        if (_settings.DownloadAutoGeneratedSubtitles)
        {
            if (_settings.Backend == BackendTypes.Ytdl)
            {
                GeneratedDownloadArguments.Add("--write-auto-sub");
            }

            if (_settings.Backend == BackendTypes.Ytdlp)
            {
                GeneratedDownloadArguments.Add("--write-auto-subs");
                // --embed-auto-subs pending https://github.com/yt-dlp/yt-dlp/issues/826
            }
        }

        if (_settings.DownloadSubtitles || _settings.DownloadSubtitlesAllLanguages || _settings.DownloadAutoGeneratedSubtitles)
        {
            GeneratedDownloadArguments.Add("--embed-subs");
        }

        if (_settings.AddMetadata)
        {
            if (_settings.Backend == BackendTypes.Ytdl)
            {
                GeneratedDownloadArguments.Add("--add-metadata");
            }

            if (_settings.Backend == BackendTypes.Ytdlp)
            {
                GeneratedDownloadArguments.Add("--embed-metadata");
            }
        }

        if (_settings.DownloadThumbnail)
        {
            GeneratedDownloadArguments.Add("--embed-thumbnail");
        }

        if (_settings.DownloadPlaylist)
        {
            GeneratedDownloadArguments.Add("--yes-playlist");

            if (!string.IsNullOrEmpty(playlistItems))
            {
                GeneratedDownloadArguments.Add("--playlist-items");
                GeneratedDownloadArguments.Add(playlistItems);
            }
        }
        else
        {
            GeneratedDownloadArguments.Add("--no-playlist");
        }

        var outputTemplate = _settings.UseCustomOutputTemplate switch
        {
            true => _settings.CustomOutputTemplate,
            false => _settings.Backend switch
            {
                BackendTypes.Ytdl => "%(title)s-%(id)s.%(ext)s",
                _ => Settings.DefaultCustomOutputTemplate,
            },
        };

        if (_settings.UseCustomPath)
        {
            outputTemplate = $@"{_settings.DownloadPath}{Path.DirectorySeparatorChar}{outputTemplate}";
        }

        if (_settings.UseCustomOutputTemplate || _settings.UseCustomPath)
        {
            GeneratedDownloadArguments.Add("-o");
            GeneratedDownloadArguments.Add(outputTemplate);
        }
    }



    /// <summary>
    /// 新增订阅频道
    /// </summary>
    /// <param name="url"></param>
    /// <returns></returns>
    private static async Task<bool> insertSubscribeChannel(string url)
    {
        var youtube = new YoutubeClient();
        var db = new SubscribeChannelContext();
        bool result = true;
        YoutubeExplode.Videos.Video video_temp = await youtube.Videos.GetAsync(url);
        db.SubscribeChannels.Add(new SubscribeChannel {
            Name = video_temp.Author.ChannelTitle,
            ChannelId = video_temp.Author.ChannelId,
            SubscribeDate = DateTimeExtensions.ConvertToChinaStandardTime(DateTime.Now)
            });
        await db.SaveChangesAsync();

        return result;
    }

    private static async Task<string> ConverVideoUrlToChannelId(string url)
    {
        var youtube = new YoutubeClient();
        YoutubeExplode.Videos.Video video_temp = await youtube.Videos.GetAsync(url);
        return video_temp.Author.ChannelId;
    }

    LoggerService loggerService = Locator.Current.GetService<LoggerService>();

    #region HomeView
    /// <summary>
    /// 开始下载（自定义参数）
    /// </summary>
    /// <param name="link"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task StartDownloadAsync(string link, CancellationToken cancellationToken = default)
    {
        Serilog.ILogger logger = loggerService.GetLogger("homeViewLogger");

        _process.StartInfo.FileName = _settings.BackendPath;
        _process.StartInfo.ArgumentList.Clear();
        _process.StartInfo.ArgumentList.AddRange(_settings.BackendGlobalArguments.Select(x => x.Argument));
        _process.StartInfo.ArgumentList.AddRange(GeneratedDownloadArguments);
        _process.StartInfo.ArgumentList.AddRange(_settings.BackendDownloadArguments.Select(x => x.Argument));
        _process.StartInfo.ArgumentList.Add(link);

        try
        {
            await RunAsync(cancellationToken, logger);
        }
        catch (Exception ex)
        {
            logger.Error(ex.Message);
        }
    }

    /// <summary>
    /// 列出可下载格式
    /// </summary>
    /// <param name="link"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task ListFormatsAsync(string link, CancellationToken cancellationToken = default)
    {
        Serilog.ILogger logger = loggerService.GetLogger("homeViewLogger");

        _process.StartInfo.FileName = _settings.BackendPath;
        _process.StartInfo.ArgumentList.Clear();
        _process.StartInfo.ArgumentList.AddRange(_settings.BackendGlobalArguments.Select(x => x.Argument));
        if (!string.IsNullOrEmpty(_settings.Proxy))
        {
            _process.StartInfo.ArgumentList.Add("--proxy");
            _process.StartInfo.ArgumentList.Add(_settings.Proxy);
        }
        _process.StartInfo.ArgumentList.Add("-F");
        _process.StartInfo.ArgumentList.Add(link);

        try
        {
            await RunAsync(cancellationToken, logger);
        }
        catch (Exception ex)
        {
            logger.Error(ex.Message);
        }
    }
    #endregion

    #region SubscribeChannelView
    /// <summary>
    /// 开始下载（固定参数：取最好的视频和音频合并成mp4文件，视频质量最高不超过1080p）
    /// </summary>
    /// <param name="link"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task StartNormalDownloadAsync(string link, CancellationToken cancellationToken = default)
    {
        //TODO 下载壁纸，单独下载这些东西，加个checkbox，下载官方字幕（自动生成 / 原channel给出）
        //TODO 要弄成选着列表的时候就可以直接下载

        Serilog.ILogger logger = loggerService.GetLogger("subscribeChannelViewLogger");

        _process.StartInfo.FileName = _settings.BackendPath;
        _process.StartInfo.ArgumentList.Clear();
        _process.StartInfo.ArgumentList.Add("--write-thumbnail"); //TODO 将壁纸转换成 png 格式的
        _process.StartInfo.ArgumentList.Add("-f bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]"); //备注：非常神奇，格式里面不能加引号，不然识别无效
        _process.StartInfo.ArgumentList.Add(link);

        try
        {
            await RunNormalDownloadAsync(cancellationToken);


            using (var context = new VideoContext())
            {
                var video = context.Videos
                                   .Where(v => v.Url == link)
                                    .FirstOrDefault();

                if (video != null)
                {
                    video.IsDownload = true; 
                    context.SaveChanges(); 
                }
                else
                {
                    logger.Error("数据库中没有该数据");
                }
            }
        }
        catch (Exception ex)
        {
            logger.Error(ex.Message);
        }
    }

    /// <summary>
    /// 开始订阅
    /// </summary>
    /// <param name="link"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task StartSubscribeAsync(string link, CancellationToken cancellationToken = default)
    {
        try
        {
            await RunSubscibeAsync(link, cancellationToken);
        }
        catch (Exception ex)
        {
            this.Log().Error(ex);
        }
    }
    /// <summary>
    /// 新增订阅频道
    /// </summary>
    /// <param name="link">视频链接</param>
    /// <param name="cancellationToken">取消令牌</param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    private async Task RunSubscibeAsync(string link, CancellationToken cancellationToken = default, string channelId = null)
    {

        var logger = loggerService.GetLogger("subscribeChannelViewLogger");

        //初始化
        var baseDB = new BaseContext();
        var videoDB = new VideoContext();
        baseDB.Database.EnsureCreated();
        Cookie myCookie = new Cookie("cookie", "XXXXXX", "/", "youtube.com"); //如果提示拉取限制，请将XXXXXX替换成自己的cookie
        IReadOnlyList<System.Net.Cookie> cookies = new List<System.Net.Cookie> { myCookie };
        var youtube = new YoutubeClient(cookies);
        Video latestVideo = null;
        DateTime latestDateTime = new DateTime();

        //获取channelId
        if (string.IsNullOrEmpty(channelId))
        {
            await insertSubscribeChannel(link);
            channelId = await ConverVideoUrlToChannelId(link);
        }

        var subscribeChannelContext = new SubscribeChannelContext();
        var subscribeChannel = subscribeChannelContext.SubscribeChannels
                           .Where(v => v.ChannelId == channelId)
                            .FirstOrDefault();

        if (subscribeChannel != null)
        {
            MessageBox.Show($"你已订阅频道：{subscribeChannel.Name}\n" +
                $"添加订阅日期为：{subscribeChannel.SubscribeDate}\n" +
                $"请勿重复添加",
                "提示", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }

        //获取频道的上传视频
        List<PlaylistVideo> videos = (List<PlaylistVideo>)await youtube.Channels.GetUploadsAsync(channelId);


        //弹窗
        string message =
            $"该频道视频总数为：{videos.Count}" +
            $"是否需要在拉取信息的同时，进行下载？" +
            $"（如选否，后续可自行下载）";
        string caption = "温馨提示";
        var result = MessageBox.Show(message, caption,
                                     MessageBoxButtons.YesNo,
                                     MessageBoxIcon.Question);

        //将视频信息写入数据库
        foreach (PlaylistVideo video in videos)
        {
            // 获取视频详情
            YoutubeExplode.Videos.Video video_temp = await youtube.Videos.GetAsync(video.Url);

            if (result == DialogResult.Yes)
            {
                await StartNormalDownloadAsync(video_temp.Url);
            }

            // 添加新的视频到数据库并保存
            videoDB.Videos.Add(new Video(video_temp));
            //{
            //    Title = video_temp.Title,
            //    Url = video_temp.Url,
            //    UploadDate = ConvertToChinaStandardTime(video_temp.UploadDate.UtcDateTime)
            //});
            await videoDB.SaveChangesAsync();

            // 记录视频信息
            logger.Information($"日期: {video_temp.UploadDate.UtcDateTime}");
            logger.Information("\t");
            logger.Information($"标题: {video_temp.Title}");
            logger.Information("\n");
        }
    }

    /// <summary>
    /// 开始更新
    /// </summary>
    /// <param name="link"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task StartPullLatestAsync(string link = null, CancellationToken cancellationToken = default, string channelId = null)
    {
        var logger = loggerService.GetLogger("subscribeChannelViewLogger");

        try
        {
            await RunPullLatestAsync(link, cancellationToken, channelId);
        }
        catch (Exception ex)
        {
            logger.Error(ex.Message);
        }
    }

    /// <summary>
    /// 拉取最新 
    /// </summary>
    /// <param name="link">视频链接</param>
    /// <param name="cancellationToken">取消令牌</param>
    /// <returns></returns>
    /// <exception cref="InvalidOperationException"></exception>
    private async Task RunPullLatestAsync(string link, CancellationToken cancellationToken = default, string channelId = null)
    {

        var logger = loggerService.GetLogger("subscribeChannelViewLogger");

        //初始化
        var baseDB = new BaseContext();
        var videoDB = new VideoContext();
        baseDB.Database.EnsureCreated();
        Cookie myCookie = new Cookie("cookie", "XXXXXX", "/", "youtube.com"); //如果提示拉取限制，请将XXXXXX替换成自己的cookie
        IReadOnlyList<System.Net.Cookie> cookies = new List<System.Net.Cookie> { myCookie };
        var youtube = new YoutubeClient(cookies);
        Video latestVideo = null;
        DateTime latestDateTime = new DateTime();

        //获取channelId
        if (string.IsNullOrEmpty(channelId))
        {
            await insertSubscribeChannel(link);
            channelId = await ConverVideoUrlToChannelId(link);
        }

        //获取数据库中最新的视频
        latestVideo = videoDB.Videos.OrderByDescending(v => v.UploadDate).FirstOrDefault();
        if (latestVideo != null)
        {
            latestDateTime = latestVideo.UploadDate;
        }
        string format = "yyyy-MM-dd HH-mm-ss";
        string latestDateTimeStr = latestDateTime.ToString(format);

        //获取频道的上传视频
        List<PlaylistVideo> videos = (List<PlaylistVideo>)await youtube.Channels.GetUploadsAsync(channelId);


        //获取需要更新的视频列表
        List<Video> newerVideos = new List<Video>();
        foreach (PlaylistVideo video in videos)
        {
            // 获取视频详情
            YoutubeExplode.Videos.Video video_temp = await youtube.Videos.GetAsync(video.Url);

            // 如果视频上传日期早于或等于最新日期，则跳出循环
            if (latestVideo != null)
            {
                if (DateTimeExtensions.ConvertToChinaStandardTime(video_temp.UploadDate.UtcDateTime) <= latestDateTime)
                {
                    break;
                }
                else
                {
                    newerVideos.Add(new Video(video_temp));
                }
            }
        }

        //弹窗
        string message =
            $"当前数据库中最新视频：{latestVideo.Title}，日期：{latestDateTimeStr}\n" +
            $"截止当前日期：{DateTime.Now.ToString(format)}，相差视频数为：{newerVideos.Count}" +
            $"是否需要在拉取信息的同时，进行下载？" +
            $"（如选否，后续可自行下载）";
        string caption = "温馨提示";
        var result = MessageBox.Show(message, caption,
                                     MessageBoxButtons.YesNo,
                                     MessageBoxIcon.Question);

        foreach (Video video in newerVideos)
        {
            if (result == DialogResult.Yes)
            {
                await StartNormalDownloadAsync(video.Url);
            }

            // 添加新的视频到数据库并保存
            videoDB.Videos.Add(video);
            await videoDB.SaveChangesAsync();

            // 记录视频信息
            logger.Information($"日期: {video.UploadDate}");
            logger.Information("\t");
            logger.Information($"标题: {video.Title}");
            logger.Information("\n");
        }
    }
    #endregion

    // 更新的异步方法
    public async Task UpdateAsync(CancellationToken cancellationToken = default)
    {
        _settings.BackendLastUpdateCheck = DateTimeOffset.Now;

        _process.StartInfo.FileName = _settings.BackendPath;
        _process.StartInfo.ArgumentList.Clear();
        if (!string.IsNullOrEmpty(_settings.Proxy))
        {
            _process.StartInfo.ArgumentList.Add("--proxy");
            _process.StartInfo.ArgumentList.Add(_settings.Proxy);
        }
        _process.StartInfo.ArgumentList.Add("-U");

        try
        {
            await RunAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            this.Log().Error(ex);
        }
    }

    // 中止的异步方法
    public async Task AbortAsync(CancellationToken cancellationToken = default)
    {
        if (CtrlCHelper.AttachConsole((uint)_process.Id))
        {
            CtrlCHelper.SetConsoleCtrlHandler(null, true);
            try
            {
                if (CtrlCHelper.GenerateConsoleCtrlEvent(CtrlCHelper.CTRL_C_EVENT, 0))
                {
                    await _process.WaitForExitAsync(cancellationToken);
                }
            }
            catch (Exception ex)
            {
                this.Log().Error(ex);
            }
            finally
            {
                CtrlCHelper.SetConsoleCtrlHandler(null, false);
                CtrlCHelper.FreeConsole();
            }
        }
        this.Log().Info("🛑 Aborted.");
    }
}
