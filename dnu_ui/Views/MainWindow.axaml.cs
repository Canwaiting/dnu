using Avalonia.Controls;
using Avalonia.Interactivity;
using Avalonia.Markup.Xaml;
using System;
using System.Diagnostics;
using System.Text;
using RestSharp;

namespace dnu_ui.Views;

public partial class MainWindow : Window
{
    private TextBox textBox;
    private TextBlock outputText;
    // 标识是否可以关闭窗口
    private bool canClose = false;

    public MainWindow()
    {
        InitializeComponent();
        textBox = this.FindControl<TextBox>("InputText");
        outputText = this.FindControl<TextBlock>("OutputText");
        OpenExe();

        // 当主窗口关闭时，确保外部进程也关闭
        this.Closing += MainWindow_Closing;
    } 
    private void InitializeComponent()
    {
        AvaloniaXamlLoader.Load(this);
    }


    public async void ClickHandler(object sender, RoutedEventArgs args)
    {
        Download(textBox.Text);
    }
 
    
    public async void Download(string youtube_url)
    {
        var options = new RestClientOptions("http://127.0.0.1:8000")
        {
            MaxTimeout = -1,
        };
        var client = new RestClient(options);
        var request = new RestRequest("/download", Method.Post);
        request.AddHeader("Content-Type", "application/json");
        var youtubeUrl = textBox.Text;
        var sb = new StringBuilder();
        sb.Append("{\n");
        sb.AppendFormat("    \"youtube_url\" : \"{0}\"\n", youtubeUrl);
        sb.Append("}");
        var body = sb.ToString(); 
        request.AddStringBody(body, DataFormat.Json);
        RestResponse response = await client.ExecuteAsync(request);
        this.outputText.Text = this.outputText.Text + "\n" + response.Content;
    }
 

    public void OpenExe()
    {
        string exePath = @".\dnu_backend.exe"; 

        try
        {
            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = exePath,
                WindowStyle = ProcessWindowStyle.Hidden, // 隐藏窗口
                CreateNoWindow = true // 不创建新窗口
            };
            Process.Start(startInfo); 

            //Process.Start(exePath); //展示窗口
        }
        catch (Exception ex)
        {
            Console.WriteLine($"无法打开文件。错误：{ex.Message}");
        } 
    }


    private void MainWindow_Closing(object sender, System.ComponentModel.CancelEventArgs e)
    {
        // 如果已经接收到回显，可以关闭窗口
        if (canClose)
        {
            return;
        }

        // 否则，取消关闭操作
        e.Cancel = true;

        // 执行同步请求
        var options = new RestClientOptions("http://127.0.0.1:8000/server/shutdown")
        {
            MaxTimeout = -1,
        };
        var client = new RestClient(options);
        var request = new RestRequest("", Method.Get);
        RestResponse response = client.Execute(request);

        // 根据请求的结果决定是否关闭窗口
        if (response.IsSuccessful && !string.IsNullOrEmpty(response.Content))
        {
            canClose = true;
            this.Close();
        }
        else
        {
            // 根据需要进行错误处理或其他逻辑
            Console.WriteLine("未接收到回显或请求失败。窗口不会关闭。");
        }
    }

}
