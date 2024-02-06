using MaterialDesignThemes.Wpf;
using ReactiveMarbles.ObservableEvents;
using ReactiveUI;
using System;
using System.Reactive.Disposables;
using System.Reactive.Linq;
using System.Windows.Controls;
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

            //TODO 重新获取数据库中对应的所有数据，否则只有重新打开应用才会更新视图中的数据


            this.WhenActivated(disposables =>
            {
                this.Bind(ViewModel, vm => vm.LabelSubscribeChannelVideoList, v => v.labelSubscribeChannelVideoList.Content).DisposeWith(disposables);

                // Link and Start
                this.BindCommand(ViewModel,
                    viewModel => viewModel.StartSubscribeCommand,
                    view => view.subscribeButton,
                    viewModel => viewModel.Link)
                    .DisposeWith(disposables);

                this.Bind(ViewModel,
                    viewModel => viewModel.Link,
                    view => view.linkTextBox.Text)
                    .DisposeWith(disposables);

                linkTextBox.Events().KeyDown
                           .Where(x => x.Key == Key.Enter)
                           .Select(_ => ViewModel!.Link)
                           .InvokeCommand(ViewModel!.StartSubscribeCommand) // Null forgiving reason: upstream limitation.
                           .DisposeWith(disposables);

                this.Bind(ViewModel,
                    viewModel => viewModel.QueuedTextBoxSink.Content,
                    view => view.resultTextBox.Text)
                    .DisposeWith(disposables);

                resultTextBox.Events().TextChanged
                             .Where(_ => WpfHelper.IsScrolledToEnd(resultTextBox))
                             .Subscribe(_ => resultTextBox.ScrollToEnd())
                             .DisposeWith(disposables);
            });
        }
    }

}
