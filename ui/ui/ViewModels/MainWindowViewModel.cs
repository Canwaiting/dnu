using System;
using System.Drawing.Printing;
using System.Net;
using System.Threading.Tasks;
using Avalonia.Threading;
using Newtonsoft.Json;
using ui.Models;

using ReactiveUI;
using RestSharp;

namespace ui.ViewModels;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Reactive;


public class MainWindowViewModel : ViewModelBase
{
    public ObservableCollection<VideoViewModel> Videos { get; } = new();
    public ReactiveCommand<Unit, Unit> DownloadCommand { get; } 
    private RestClientOptions options = new RestClientOptions("http://127.0.0.1:8000")
    {
        MaxTimeout = -1,
    };   
    
    private string? _labelContent; 
    public string? LabelContent
    {
        get => _labelContent;
        set => this.RaiseAndSetIfChanged(ref _labelContent, value);
    }
    
    
    private string? _youtubeUrlText; 
    public string? YoutubeUrlText
    {
        get => _youtubeUrlText;
        set => this.RaiseAndSetIfChanged(ref _youtubeUrlText, value);
    }

    
    private bool _isBusy;
    public bool IsBusy
    {
        get => _isBusy;
        set => this.RaiseAndSetIfChanged(ref _isBusy, value);
    }
    
    private bool _isNotBusy;
    public bool IsNotBusy
    {
        get => !_isBusy;
        set => this.RaiseAndSetIfChanged(ref _isNotBusy, value);
    }

    public int _downloadPercent = 0;
    public int DownloadPercent
    {
        get => _downloadPercent;
        set => this.RaiseAndSetIfChanged(ref _downloadPercent, value);
    }

    public MainWindowViewModel()
    {
        DownloadCommand = ReactiveCommand.Create(() =>
        {
            Console.WriteLine($"开始下载：{YoutubeUrlText}");
            DoDownload(YoutubeUrlText); 
        });
    }

    private async void DoDownload(string youtubeurltext)
    {
        try
        {
            IsBusy = true; 
        
            var client = new RestClient(options);
            var request = new RestRequest("/download", Method.Post);
            request.AddHeader("Content-Type", "application/json");
            request.AddHeader("Content-Type", "application/x-www-form-urlencoded");
            request.AddParameter("youtube_url", youtubeurltext);
            RestResponse response = client.Execute(request);
        
            if (response.StatusCode == HttpStatusCode.OK)
            {
                ApiResponse responseObj = JsonConvert.DeserializeObject<ApiResponse>(response.Content);
                if (responseObj.Code == 0)
                {
                    // 启动作业并立即返回
                    Dispatcher.UIThread.Post(() => GetDonwloadProgress(youtubeurltext), 
                        DispatcherPriority.Background); 
                }
            }
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
    } 
    
    private async Task GetDonwloadProgress(string youtubeurltext)
    {
        try
        {
            bool is_running = true;
            while (is_running)
            { 
                await Task.Delay(1000);
                var client = new RestClient(options);
                var request = new RestRequest($"/download/progress?youtube_url={youtubeurltext}", Method.Get); 
                RestResponse response = client.Execute(request);

                if (response.StatusCode == HttpStatusCode.OK)
                {
                    ApiResponse responseObj = JsonConvert.DeserializeObject<ApiResponse>(response.Content);
                    if (responseObj.Code == 0)
                    {
                        DownloadInfo downloadInfo = JsonConvert.DeserializeObject<DownloadInfo>(responseObj.Data.ToString());
                        Console.WriteLine($"百分比：{downloadInfo.Percent}");
                        DownloadPercent = downloadInfo.Percent;
                        LabelContent = downloadInfo.StatusMessage;
                        if (downloadInfo.Percent == 100)
                        {
                            is_running = false;
                            IsBusy = false;
                        } 
                    }
                }
            }
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }
    }

}