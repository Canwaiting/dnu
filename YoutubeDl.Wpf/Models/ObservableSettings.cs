﻿using MaterialDesignThemes.Wpf;
using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;

namespace YoutubeDl.Wpf.Models;

public class ObservableSettings : ReactiveObject
{
    // 应用设置
    public Settings AppSettings { get; }

    // 应用颜色模式
    public BaseTheme AppColorMode { get; set; }

    // 窗口宽度
    [Reactive]
    public double WindowWidth { get; set; }

    // 窗口高度
    [Reactive]
    public double WindowHeight { get; set; }

    // 后端类型
    [Reactive]
    public BackendTypes Backend { get; set; }

    // 后端路径
    [Reactive]
    public string BackendPath { get; set; }

    // 后端全局参数
    public ObservableCollection<BackendArgument> BackendGlobalArguments { get; set; }

    // 后端下载参数
    public List<BackendArgument> BackendDownloadArguments { get; set; }

    // 后端自动更新
    [Reactive]
    public bool BackendAutoUpdate { get; set; }

    // 后端最后更新检查
    [Reactive]
    public DateTimeOffset BackendLastUpdateCheck { get; set; }

    // Ffmpeg路径
    [Reactive]
    public string FfmpegPath { get; set; }

    // 代理
    [Reactive]
    public string Proxy { get; set; }

    // 日志最大条目
    [Reactive]
    public int LoggingMaxEntries { get; set; }

    // 选定的预设
    [Reactive]
    public Preset? SelectedPreset { get; set; }

    // 选定的预设文本
    [Reactive]
    public string SelectedPresetText { get; set; }

    // 自定义预设
    public List<Preset> CustomPresets { get; set; }

    // 添加元数据
    [Reactive]
    public bool AddMetadata { get; set; }

    // 下载缩略图
    [Reactive]
    public bool DownloadThumbnail { get; set; }

    // 下载字幕
    [Reactive]
    public bool DownloadSubtitles { get; set; }

    // 下载所有语言的字幕
    [Reactive]
    public bool DownloadSubtitlesAllLanguages { get; set; }

    // 下载自动生成的字幕
    [Reactive]
    public bool DownloadAutoGeneratedSubtitles { get; set; }

    // 下载播放列表
    [Reactive]
    public bool DownloadPlaylist { get; set; }

    // 使用自定义输出模板
    [Reactive]
    public bool UseCustomOutputTemplate { get; set; }

    // 自定义输出模板
    [Reactive]
    public string CustomOutputTemplate { get; set; }

    // 输出模板历史
    public List<string> OutputTemplateHistory { get; }

    // 使用自定义路径
    [Reactive]
    public bool UseCustomPath { get; set; }

    // 下载路径
    [Reactive]
    public string DownloadPath { get; set; }

    // 下载路径历史
    public List<string> DownloadPathHistory { get; }

    public ObservableSettings(Settings settings)
    {
        AppSettings = settings; // 设置应用设置
        AppColorMode = settings.AppColorMode; // 设置应用颜色模式
        WindowWidth = settings.WindowWidth; // 设置窗口宽度
        WindowHeight = settings.WindowHeight; // 设置窗口高度
        Backend = settings.Backend; // 设置后端类型
        BackendPath = settings.BackendPath;
        FfmpegPath = settings.FfmpegPath;
        BackendGlobalArguments = new(settings.BackendGlobalArguments); // 设置后端全局参数
        BackendDownloadArguments = new(settings.BackendDownloadArguments); // 设置后端下载参数
        BackendAutoUpdate = settings.BackendAutoUpdate; // 设置后端自动更新
        BackendLastUpdateCheck = settings.BackendLastUpdateCheck; // 设置后端最后更新检查时间
        Proxy = settings.Proxy; // 设置代理
        LoggingMaxEntries = settings.LoggingMaxEntries; // 设置日志最大条目数
        SelectedPreset = settings.SelectedPreset; // 设置选定的预设
        SelectedPresetText = settings.SelectedPreset.DisplayName; // 设置选定预设的显示名称
        CustomPresets = new(settings.CustomPresets); // 设置自定义预设
        AddMetadata = settings.AddMetadata; // 设置是否添加元数据
        DownloadThumbnail = settings.DownloadThumbnail; // 设置是否下载缩略图
        DownloadSubtitles = settings.DownloadSubtitles; // 设置是否下载字幕
        DownloadSubtitlesAllLanguages = settings.DownloadSubtitlesAllLanguages; // 设置是否下载所有语言的字幕
        DownloadAutoGeneratedSubtitles = settings.DownloadAutoGeneratedSubtitles; // 设置是否下载自动生成的字幕
        DownloadPlaylist = settings.DownloadPlaylist; // 设置是否下载播放列表
        UseCustomOutputTemplate = settings.UseCustomOutputTemplate; // 设置是否使用自定义输出模板
        CustomOutputTemplate = settings.CustomOutputTemplate; // 设置自定义输出模板
        OutputTemplateHistory = new(settings.OutputTemplateHistory); // 设置输出模板历史
        UseCustomPath = settings.UseCustomPath; // 设置是否使用自定义路径
        DownloadPath = settings.DownloadPath; // 设置下载路径
        DownloadPathHistory = new(settings.DownloadPathHistory); // 设置下载路径历史
    }

    public void UpdateAppSettings()
    {
        AppSettings.AppColorMode = AppColorMode; // 更新应用颜色模式
        AppSettings.WindowWidth = WindowWidth; // 更新窗口宽度
        AppSettings.WindowHeight = WindowHeight; // 更新窗口高度
        AppSettings.Backend = Backend; // 更新后端类型
        AppSettings.BackendPath = BackendPath; // 更新后端路径
        AppSettings.BackendGlobalArguments = BackendGlobalArguments.ToArray(); // 更新后端全局参数
        AppSettings.BackendDownloadArguments = BackendDownloadArguments.ToArray(); // 更新后端下载参数
        AppSettings.BackendAutoUpdate = BackendAutoUpdate; // 更新后端自动更新设置
        AppSettings.BackendLastUpdateCheck = BackendLastUpdateCheck; // 更新后端最后更新检查时间
        AppSettings.FfmpegPath = FfmpegPath; // 更新Ffmpeg路径
        AppSettings.Proxy = Proxy; // 更新代理设置
       // AppSettings.LoggingMaxEntries is managed by the validation handler.
        AppSettings.SelectedPreset = SelectedPreset ?? Preset.Auto; // 更新选定的预设
        AppSettings.CustomPresets = CustomPresets.ToArray(); // 更新自定义预设
        AppSettings.AddMetadata = AddMetadata; // 更新添加元数据设置
        AppSettings.DownloadThumbnail = DownloadThumbnail; // 更新下载缩略图设置
        AppSettings.DownloadSubtitles = DownloadSubtitles; // 更新下载字幕设置
        AppSettings.DownloadSubtitlesAllLanguages = DownloadSubtitlesAllLanguages; // 更新下载所有语言字幕设置
        AppSettings.DownloadAutoGeneratedSubtitles = DownloadAutoGeneratedSubtitles; // 更新下载自动生成字幕设置
        AppSettings.DownloadPlaylist = DownloadPlaylist; // 更新下载播放列表设置
        AppSettings.UseCustomOutputTemplate = UseCustomOutputTemplate; // 更新使用自定义输出模板设置
        AppSettings.CustomOutputTemplate = CustomOutputTemplate; // 更新自定义输出模板
        AppSettings.UseCustomPath = UseCustomPath; // 更新使用自定义路径设置
        AppSettings.OutputTemplateHistory = OutputTemplateHistory.ToArray(); // 更新输出模板历史
        AppSettings.DownloadPath = DownloadPath; // 更新下载路径
        AppSettings.DownloadPathHistory = DownloadPathHistory.ToArray(); // 更新下载路径历史
    }

}
