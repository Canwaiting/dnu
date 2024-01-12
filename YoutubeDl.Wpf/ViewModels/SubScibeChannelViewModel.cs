using DynamicData;
using MaterialDesignThemes.Wpf;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using ReactiveUI.Validation.Extensions;
using ReactiveUI.Validation.Helpers;
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Reactive;
using System.Reactive.Linq;
using System.Reflection;
using System.Threading.Tasks;
using System.Threading;
using YoutubeDl.Wpf.Models;
using YoutubeDl.Wpf.Utils;
using static System.Windows.Forms.LinkLabel;

namespace YoutubeDl.Wpf.ViewModels
{
    public class SubScibeChannelViewModel : ReactiveValidationObject
    {
        public ReactiveCommand<string, Unit> StartDownloadCommand { get; }
        public BackendService BackendService { get; }
        public BackendInstance BackendInstance { get; }
        public QueuedTextBoxSink QueuedTextBoxSink { get; }



        public SubScibeChannelViewModel(ObservableSettings settings, BackendService backendService, ISnackbarMessageQueue snackbarMessageQueue)
        {
            BackendService = backendService;
            BackendInstance = backendService.CreateInstance();

            StartDownloadCommand = ReactiveCommand.CreateFromTask<string>(async (functionName) =>
            {
                // Your custom logic here
                Console.WriteLine($"成功触发{functionName}");
                BackendInstance.PingAsync();
            });

        }
    }
}
