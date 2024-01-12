using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using Splat;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Shell;

namespace YoutubeDl.Wpf.Models;

// 后端服务类
public class BackendService : ReactiveObject, IEnableLogger
{
    // ObservableSettings实例
    private readonly ObservableSettings _settings;

    // 后端实例列表
    public List<BackendInstance> Instances { get; } = new();

    // 是否可以更新的标志
    [Reactive]
    public bool CanUpdate { get; set; } = true;

    // 全局下载进度百分比，0.99表示99%
    [Reactive]
    public double GlobalDownloadProgressPercentage { get; set; }

    // 任务栏项目进度状态
    [Reactive]
    public TaskbarItemProgressState ProgressState { get; set; }

    // 构造函数，接收一个ObservableSettings实例
    public BackendService(ObservableSettings settings) => _settings = settings;

    // 创建一个新的后端实例
    public BackendInstance CreateInstance()
    {
        var instance = new BackendInstance(_settings, this);
        Instances.Add(instance);
        return instance;
    }

    // 更新进度
    public void UpdateProgress()
    {
        // 所有实例都不在运行时，可以更新
        CanUpdate = Instances.All(x => !x.IsRunning);

        // 计算全局下载进度百分比
        GlobalDownloadProgressPercentage = Instances.Sum(x => x.DownloadProgressPercentage) / Instances.Count;

        // 设置任务栏项目进度状态
        if (Instances.All(x => x.StatusIndeterminate))
        {
            ProgressState = TaskbarItemProgressState.Indeterminate;
        }
        else if (GlobalDownloadProgressPercentage > 0.0)
        {
            ProgressState = TaskbarItemProgressState.Normal;
        }
        else
        {
            ProgressState = TaskbarItemProgressState.None;
        }
    }

    // 异步更新后端
    public Task UpdateBackendAsync(CancellationToken cancellationToken = default)
    {
        var tasks = Instances.Select(x => x.UpdateAsync(cancellationToken));
        return Task.WhenAll(tasks);
    }
}
