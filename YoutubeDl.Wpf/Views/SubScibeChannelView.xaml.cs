using MaterialDesignThemes.Wpf;
using ReactiveMarbles.ObservableEvents;
using ReactiveUI;
using System;
using System.Reactive.Disposables;
using System.Reactive.Linq;
using System.Windows.Input;
using System.Windows.Shell;
using YoutubeDl.Wpf.Utils;

namespace YoutubeDl.Wpf.Views
{
    /// <summary>
    /// SubScibeChannelView.xaml 的交互逻辑
    /// </summary>
    public partial class SubScibeChannelView
    {
        public SubScibeChannelView()
        {
            InitializeComponent();

            this.WhenActivated(disposables =>
            {
                this.BindCommand(ViewModel,
                    viewModel => viewModel.StartDownloadCommand,
                    view => view.downloadButton)
                    .DisposeWith(disposables);

            });
        }
    }
}
