using DynamicData;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using Splat;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using YoutubeDl.Wpf.Utils;

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
    private async Task MyRunAsync()
    {
        if (!_myprocess.Start())
            throw new InvalidOperationException("Method called when the backend process is running.");

        //SetStatusRunning();

        await Task.WhenAll(
            MyReadAndParseLinesAsync(_myprocess.StandardError),
            MyReadAndParseLinesAsync(_myprocess.StandardOutput),
            _myprocess.WaitForExitAsync());

        //SetStatusStopped();
    }

    // 异步运行方法
    private async Task RunAsync(CancellationToken cancellationToken = default)
    {
        if (!_process.Start())
            throw new InvalidOperationException("Method called when the backend process is running.");

        SetStatusRunning();

        await Task.WhenAll(
            ReadAndParseLinesAsync(_process.StandardError, cancellationToken),
            ReadAndParseLinesAsync(_process.StandardOutput, cancellationToken),
            _process.WaitForExitAsync(cancellationToken));

        SetStatusStopped();
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
    private async Task MyReadAndParseLinesAsync(StreamReader reader, CancellationToken cancellationToken = default)
    {
        while (true)
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (line is null)
                return;

            var loggerService = Locator.Current.GetService<LoggerService>();
            var loggernew = loggerService.GetLogger("loggernew");
            loggernew.Information(line);
        }
    }

    // 异步读取和解析行
    private async Task ReadAndParseLinesAsync(StreamReader reader, CancellationToken cancellationToken = default)
    {
        while (true)
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (line is null)
                return;

            var loggerService = Locator.Current.GetService<LoggerService>();
            var logger = loggerService.GetLogger("logger");
            logger.Information(line);
            //this.Log().Info(line);
            //this.Log().Info("Hello world");
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

    // 开始下载的异步方法
    public async Task PingAsync()
    {
        _myprocess.StartInfo.FileName = "cmd.exe";
        _myprocess.StartInfo.ArgumentList.Clear();
        _myprocess.StartInfo.ArgumentList.Add("/c");
        _myprocess.StartInfo.ArgumentList.Add("ping www.baidu.com");

        try
        {
            await MyRunAsync();
        }
        catch (Exception ex)
        {
            this.Log().Error(ex);
        }
    }

    // 开始下载的异步方法
    public async Task StartDownloadAsync(string link, CancellationToken cancellationToken = default)
    {
        _process.StartInfo.FileName = _settings.BackendPath;
        _process.StartInfo.ArgumentList.Clear();
        _process.StartInfo.ArgumentList.AddRange(_settings.BackendGlobalArguments.Select(x => x.Argument));
        _process.StartInfo.ArgumentList.AddRange(GeneratedDownloadArguments);
        _process.StartInfo.ArgumentList.AddRange(_settings.BackendDownloadArguments.Select(x => x.Argument));
        _process.StartInfo.ArgumentList.Add(link);

        try
        {
            await RunAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            this.Log().Error(ex);
        }
    }

    // 列出格式的异步方法
    public async Task ListFormatsAsync(string link, CancellationToken cancellationToken = default)
    {
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
            await RunAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            this.Log().Error(ex);
        }
    }

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
