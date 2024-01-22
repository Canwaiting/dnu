using ReactiveUI;
using ReactiveUI.Fody.Helpers;
using Serilog;
using Serilog.Core;
using Serilog.Events;
using System;
using System.Collections.Generic;
using System.Reactive.Concurrency;

namespace YoutubeDl.Wpf.Models;

public class QueuedTextBoxSink : ReactiveObject, ILogEventSink
{
    private readonly object _locker = new();
    private readonly Settings _settings;
    private readonly Queue<string> _queuedLogMessages;
    private readonly IFormatProvider? _formatProvider;
    private int _contentLength;

    [Reactive]
    public string Content { get; set; } = "";

    public QueuedTextBoxSink(Settings settings, IFormatProvider? formatProvider = null)
    {
        _settings = settings;
        _queuedLogMessages = new(settings.LoggingMaxEntries);
        _formatProvider = formatProvider;
    }

    public void Emit(LogEvent logEvent)
    {
        // 针对https://github.com/reactiveui/ReactiveUI/issues/3415的问题的解决方法，直到上游有修复
        if (logEvent.MessageTemplate.Text.EndsWith(" is a POCO type and won't send change notifications, WhenAny will only return a single value!", StringComparison.Ordinal))
        {
            return;
        }

        var renderedMessage = logEvent.RenderMessage(_formatProvider);

        var message = logEvent.RenderMessage(_formatProvider);
        //// 2023-04-24T10:24:00.000+00:00 [I] Hi!
        //var length = 29 + 1 + 3 + 1 + renderedMessage.Length + Environment.NewLine.Length;
        //var message = string.Create(length, logEvent, (buf, logEvent) =>
        //{
        //    // 如果无法格式化时间戳，抛出异常
        //    if (!logEvent.Timestamp.TryFormat(buf, out var charsWritten, "yyyy-MM-ddTHH:mm:ss.fffzzz"))
        //        throw new Exception("Failed to format timestamp for log message.");
        //    // 如果格式化的时间戳长度不是29，抛出异常
        //    if (charsWritten != 29)
        //        throw new Exception($"Unexpected formatted timestamp length {charsWritten}.");

        //    buf[29] = ' ';
        //    buf[30] = '[';
        //    // 根据日志级别，设置对应的字符
        //    buf[31] = logEvent.Level switch
        //    {
        //        LogEventLevel.Verbose => 'V',
        //        LogEventLevel.Debug => 'D',
        //        LogEventLevel.Information => 'I',
        //        LogEventLevel.Warning => 'W',
        //        LogEventLevel.Error => 'E',
        //        LogEventLevel.Fatal => 'F',
        //        _ => '?',
        //    };
        //    buf[32] = ']';
        //    buf[33] = ' ';
        //    // 将渲染的消息复制到缓冲区
        //    renderedMessage.CopyTo(buf[34..]);
        //    // 将换行符复制到缓冲区
        //    Environment.NewLine.CopyTo(buf[(34 + renderedMessage.Length)..]);
        //});

        lock (_locker)
        {
            // 当队列中的日志消息数量大于或等于设置的最大条目数时，进行循环
            while (_queuedLogMessages.Count >= _settings.LoggingMaxEntries)
            {
                // 出队一条消息
                var dequeuedMessage = _queuedLogMessages.Dequeue();
                // 更新内容长度
                _contentLength -= dequeuedMessage.Length;
            }

            // 将新的消息加入队列
            _queuedLogMessages.Enqueue(message);
            // 更新内容长度
            _contentLength += message.Length;

            // 创建一个新的字符串，内容为队列中的所有消息
            var content = string.Create(_contentLength, _queuedLogMessages, (buf, msgs) =>
            {
                // 遍历队列中的每一条消息
                foreach (var msg in msgs)
                {
                    // 将消息复制到缓冲区
                    msg.CopyTo(buf);
                    // 更新缓冲区
                    buf = buf[msg.Length..];
                }
            });

            // 在主线程中更新Content的值
            RxApp.MainThreadScheduler.Schedule(() =>
            {
                Content = content;
            });
        }

    }
}
