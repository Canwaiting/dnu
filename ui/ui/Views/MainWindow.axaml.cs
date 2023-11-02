using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Threading;
using Newtonsoft.Json;
using RestSharp;

namespace ui.Views;

public partial class MainWindow : Window
{
    private TextBox myTextBox;
    private Button myButton;
    private Label myLabel;
    private ProgressBar myProgressBar;
    private string DNUServerHost = "http://127.0.0.1:8000";
    private string API_SHUTDOWN = "/server/shutdown";
    private string youtube_id; 
    
    public MainWindow()
    {
        InitializeComponent(); 
        myTextBox = this.Get<TextBox>("TextBoxYoutubeUrl");
        myLabel = this.Get<Label>("MyLabel");
        myProgressBar = this.Get<ProgressBar>("MyProgressBar");
        myButton = this.Get<Button>("MyButton");
    } 
    
    private async Task GetInfo()
    {
        bool is_running = true;
        while (is_running)
        {

            await Task.Delay(1000);
            var options = new RestClientOptions(DNUServerHost)
            {
                MaxTimeout = -1,
            };
            var client = new RestClient(options);
            var request = new RestRequest("/getinfo", Method.Post);
            request.AddHeader("Content-Type", "application/json");
            var body = new
            {
                value = youtube_id
            };

            request.AddJsonBody(body);
            RestResponse response = client.Execute(request);

            if (response.StatusCode == HttpStatusCode.OK)
            {
                var data = JsonConvert.DeserializeObject<Dictionary<string, string>>(response.Content);
                if (data != null)
                {
                    string progress_value = data["message"];
                    this.myProgressBar.Value = Convert.ToInt32(progress_value);
                    myLabel.Content = "下载中...";
                    if (this.myProgressBar.Value == 100)
                    {
                        is_running = false;
                        myButton.IsEnabled = true; 
                        myTextBox.IsEnabled = true; 
                        myLabel.Content = "下载完成";
                    }
                }
            }
        }
    }

    private void Button_OnClick(object? sender, RoutedEventArgs e)
    {
        var options = new RestClientOptions(DNUServerHost)
        {
            MaxTimeout = -1,
        };
        var client = new RestClient(options);
        var request = new RestRequest("/download/all", Method.Post);
        request.AddHeader("Content-Type", "application/json");
        var body = new 
        {
            value = this.myTextBox.Text
        };
        
        request.AddJsonBody(body);
        RestResponse response = client.Execute(request);
        
        if (response.StatusCode == HttpStatusCode.OK)
        {
            var data = JsonConvert.DeserializeObject<Dictionary<string, string>>(response.Content);
            if (data != null && data.ContainsKey("message"))
            {
                // Console.WriteLine("Message: " + data["message"]);
                youtube_id = data["message"];
                Console.WriteLine("youtubeid：" + youtube_id);
            }
            myLabel.Content = "下载中...";
            myTextBox.IsEnabled = false; 
            myButton.IsEnabled = false; 
            
            // 启动作业并立即返回
            Dispatcher.UIThread.Post(() => GetInfo(), 
                DispatcherPriority.Background);
        }
    }
}