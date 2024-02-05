using MaterialDesignThemes.Wpf;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using Serilog;
using Splat;
//using Splat.Serilog;
using System;
using System.ComponentModel;
using System.Threading;
using System.Threading.Tasks;
using YoutubeDl.Wpf.Models;

namespace YoutubeDl.Wpf.ViewModels
{
    // MainWindowViewModel类，继承自ReactiveObject
    public class MainWindowViewModel : ReactiveObject
    {
        // 定义私有只读字段，用于消息队列
        private readonly ISnackbarMessageQueue _snackbarMessageQueue;
        // 定义私有只读字段，用于设置
        private readonly Settings _settings;

        // 公共属性，用于共享设置
        public ObservableSettings SharedSettings { get; }
        // 公共属性，用于后端服务
        public BackendService BackendService { get; }
        // 公共属性，用于预设对话框视图模型
        public PresetDialogViewModel PresetDialogVM { get; }
        // 公共属性，用于标签页
        public object[] Tabs { get; }

        // 使用Reactive特性，定义公共属性，用于判断对话框是否打开
        [Reactive]
        public bool IsDialogOpen { get; set; }

        // 公共属性，用于保存设置的异步命令
        public ReactiveCommand<CancelEventArgs?, bool> SaveSettingsAsyncCommand { get; }

        // MainWindowViewModel构造函数
        public MainWindowViewModel(ISnackbarMessageQueue snackbarMessageQueue)
        {
            // 初始化消息队列
            _snackbarMessageQueue = snackbarMessageQueue;

            // 尝试加载设置
            try
            {
                _settings = Settings.LoadAsync().GetAwaiter().GetResult();
            }
            catch (Exception ex)
            {
                // 加载失败，将异常消息加入消息队列，并初始化设置
                snackbarMessageQueue.Enqueue(ex.Message);
                _settings = new();
            }

            // 配置日志
            var queuedTextBoxsink = new QueuedTextBoxSink(_settings);
            var queuedTextBoxsinknew = new QueuedTextBoxSink(_settings);
            Serilog.ILogger homViewLogger = new LoggerConfiguration()
                .WriteTo.Sink(queuedTextBoxsink)
                .CreateLogger();
            Serilog.ILogger subscribeChannelViewLogger = new LoggerConfiguration()
                .WriteTo.Sink(queuedTextBoxsinknew)
                .CreateLogger();
            LoggerService loggerService = new LoggerService();
            loggerService.AddLogger("homViewLogger", homViewLogger);
            loggerService.AddLogger("subscribeChannelViewLogger", subscribeChannelViewLogger);
            Locator.CurrentMutable.RegisterConstant(loggerService, typeof(LoggerService));

            // 初始化共享设置、后端服务、预设对话框视图模型和标签页
            SharedSettings = new(_settings);
            BackendService = new(SharedSettings);
            PresetDialogVM = new(ControlDialog);
            Tabs = new object[]
            {
                new SubScibeChannelViewModel(SharedSettings, BackendService,queuedTextBoxsinknew, snackbarMessageQueue),
                new HomeViewModel(SharedSettings, BackendService, queuedTextBoxsink, PresetDialogVM, snackbarMessageQueue),
                new SettingsViewModel(SharedSettings, BackendService, snackbarMessageQueue),
            };

            // 初始化保存设置的异步命令
            SaveSettingsAsyncCommand = ReactiveCommand.CreateFromTask<CancelEventArgs?, bool>(SaveSettingsAsync);
        }

        // 控制对话框的打开和关闭
        private void ControlDialog(bool open) => IsDialogOpen = open;

        // 保存设置的异步方法
        private async Task<bool> SaveSettingsAsync(CancelEventArgs? cancelEventArgs = null, CancellationToken cancellationToken = default)
        {
            // 更新应用设置
            SharedSettings.UpdateAppSettings();

            // 尝试保存设置
            try
            {
                await _settings.SaveAsync(cancellationToken);
            }
            catch (Exception ex)
            {
                // 保存失败，将异常消息加入消息队列，并取消窗口关闭
                _snackbarMessageQueue.Enqueue(ex.Message);
                if (cancelEventArgs is not null)
                    cancelEventArgs.Cancel = true;

                return false;
            }

            return true;
        }
    }
}
