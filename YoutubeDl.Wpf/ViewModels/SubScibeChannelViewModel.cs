﻿using DynamicData;
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
using System.Collections.Generic;
using YoutubeExplode.Channels;
using System.Threading.Channels;

namespace YoutubeDl.Wpf.ViewModels
{
    public class SubScibeChannelViewModel : ReactiveValidationObject
    {
        public ReactiveCommand<string, Unit> StartSubscribeCommand { get; }

        private ObservableCollection<Video> _videoList;
        public ObservableCollection<Video> VideoList
        {
            get => _videoList;
            set => this.RaiseAndSetIfChanged(ref _videoList, value);
        }

        private ObservableCollection<SubscribeChannel> _subscribeChannelList;
        public ObservableCollection<SubscribeChannel> SubscribeChannelList
        {
            get => _subscribeChannelList;
            set => this.RaiseAndSetIfChanged(ref _subscribeChannelList, value);
        }

        private ObservableCollection<Video> _subscribeChannelVideoList;
        public ObservableCollection<Video> SubscribeChannelVideoList
        {
            get => _subscribeChannelVideoList;
            set => this.RaiseAndSetIfChanged(ref _subscribeChannelVideoList, value);
        }


        [Reactive]
        public string Link { get; set; } = "";

        public BackendService BackendService { get; }
        public BackendInstance BackendInstance { get; }
        public QueuedTextBoxSink QueuedTextBoxSink { get; }

        private ReactiveCommand<Video, Unit> _normalingleDownloadCommand;

        public ReactiveCommand<Video, Unit> NormalDownloadCommand
        {
            get { return _normalingleDownloadCommand; }
            set { this.RaiseAndSetIfChanged(ref _normalingleDownloadCommand, value); }
        }

        private ReactiveCommand<SubscribeChannel, Unit> _pullLatestCommand;

        public ReactiveCommand<SubscribeChannel, Unit> PullLatestCommand
        {
            get { return _pullLatestCommand; }
            set { this.RaiseAndSetIfChanged(ref _pullLatestCommand, value); }
        }

        private async void PullLatest(SubscribeChannel currentRow)
        {
            await BackendInstance.StartPullLatestAsync(channelId : currentRow.ChannelId);
        }


        /// <summary>
        /// 普通下载（最高1080p + 最好音质 合并输出mp4）
        /// yt-dlp -f "bestvideo[height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 -o "%(title)s.%(ext)s" 视频链接
        /// </summary>
        /// <param name="currentRow"></param>
        private async void NormalDownload(Video currentRow)
        {
            await BackendInstance.StartNormalDownloadAsync(currentRow.Url);
        }

        public SubScibeChannelViewModel(ObservableSettings settings, BackendService backendService, QueuedTextBoxSink queuedTextBoxSink, ISnackbarMessageQueue snackbarMessageQueue)
        {
            PullLatestCommand = ReactiveCommand.Create<SubscribeChannel>(PullLatest);
            NormalDownloadCommand = ReactiveCommand.Create<Video>(NormalDownload);



            BackendService = backendService;
            BackendInstance = backendService.CreateInstance();
            QueuedTextBoxSink = queuedTextBoxSink;
            VideoList = GetVideoList();
            SubscribeChannelList = GetSubscribeChannelList();
            SubscribeChannelVideoList = GetSubscribeChannelVideoList(channelId: "hello world");

            var canRun = this.WhenAnyValue( x => x.Link, (link) => !string.IsNullOrEmpty(link));
            StartSubscribeCommand = ReactiveCommand.CreateFromTask<string>(StartSubscribeAsync, canRun);
        }
        
        private ObservableCollection<Video> GetVideoList()
        {

            ObservableCollection<Video> result = new ObservableCollection<Video>();
            var baseDB = new BaseContext();
            baseDB.Database.EnsureCreated();
            var videoDB = new VideoContext();
            result = new ObservableCollection<Video>(videoDB.Videos.ToList());
            return result;
        }

        private ObservableCollection<SubscribeChannel> GetSubscribeChannelList()
        {
            ObservableCollection<SubscribeChannel> result = new ObservableCollection<SubscribeChannel>();
            var baseDB = new BaseContext();
            baseDB.Database.EnsureCreated();
            var subscribeChannelDB = new SubscribeChannelContext();
            result = new ObservableCollection<SubscribeChannel>(subscribeChannelDB.SubscribeChannels.ToList());
            return result;
        }

        private ObservableCollection<Video> GetSubscribeChannelVideoList(string channelId = null)
        {
            ObservableCollection<Video> result = new ObservableCollection<Video>();
            var baseDB = new BaseContext();
            baseDB.Database.EnsureCreated();
            var VideoDB = new VideoContext();
            result = new ObservableCollection<Video>(VideoDB.Videos.ToList());
            return result;
        }


        private Task StartSubscribeAsync(string link, CancellationToken cancellationToken = default)
        {
            return BackendInstance.StartSubscribeAsync(link, cancellationToken);
        }


    }
}
