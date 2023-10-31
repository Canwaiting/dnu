using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using RestSharp;

namespace ui.Views;

public partial class MainWindow : Window
{
    private string DNUServerName = "dnu_backend";  // 填在 Resources.resc 中的名字
    private string DNUServerHost = "http://127.0.0.1:8000";
    private string API_SHUTDOWN = "/server/shutdown";
        
    public MainWindow()
    {
        InitializeComponent(); 
        StartDNUServer();
        
        this.Closing += CloseWindow;
    }

    public void StartDNUServer()
    {
        try
        {
            string exeFileName = Path.Combine(Directory.GetCurrentDirectory(), DNUServerName);
            File.Delete(exeFileName); 
            using (FileStream fsDst = new FileStream(exeFileName, 
                       FileMode.CreateNew, FileAccess.Write))
            {
                byte[] bytes = ui.Resources.Getdnu_backend();
                fsDst.Write(bytes, 0, bytes.Length);
            } 
            
            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = exeFileName,
                WindowStyle = ProcessWindowStyle.Hidden, // 隐藏窗口
                CreateNoWindow = true // 不创建新窗口
            };
            Process.Start(startInfo); 
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
        } 
    }

    public void CloseWindow(object sender, System.ComponentModel.CancelEventArgs e)
    { 
        ShutdownDNUServer(); 
        Environment.Exit(0); 
    }

    public void ShutdownDNUServer()
    {
        try
        {
            var options = new RestClientOptions(DNUServerHost + API_SHUTDOWN)
            {
                MaxTimeout = -1,
            };
            var client = new RestClient(options);
            var request = new RestRequest("", Method.Get);
            /*
            TODO
            现在只要是发送了，就不管你这么多 
            后面要考虑内存泄漏这些东西 
            */
            RestResponse response = client.Execute(request);  
        }
        catch (Exception ex)
        {
            Console.WriteLine(ex.Message);
        } 

    }
}