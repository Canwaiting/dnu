namespace ui.Models;
using System;
using Newtonsoft.Json;
using System.Collections.Generic;

public class models
{
    
}

// 表示最外层的JSON响应
public class ApiResponse
{
    [JsonProperty("code")]
    public int Code { get; set; }

    [JsonProperty("message")]
    public string Message { get; set; }

    [JsonProperty("data")]
    public Object Data { get; set; }
}

public class DownloadInfo
{
    [JsonProperty("status")]
    public string Status{ get; set; } 

    [JsonProperty("percent")]
    public int Percent{ get; set; }
    
    [JsonProperty("status_message")]
    public string StatusMessage{ get; set; }
}



// public class 
// {
//     [JsonProperty("code")]
//     public int Code { get; set; }
//
//     [JsonProperty("message")]
//     public string Message { get; set; }
//
//     [JsonProperty("data")]
//     public Object Data { get; set; }
// }

// // 表示"data"字段内的结构
// public class Data
// {
//     [JsonProperty("len")]
//     public int Len { get; set; }
//
//     [JsonProperty("subscribechannels")]
//     public List<SubscribeChannel> SubscribeChannels { get; set; }
// }
//
// // 表示"subscribechannels"数组中的项
// public class SubscribeChannel
// {
//     [JsonProperty("id")]
//     public int Id { get; set; }
//
//     [JsonProperty("channel_name")]
//     public string ChannelName { get; set; }
//
//     [JsonProperty("channel_id")]
//     public string ChannelId { get; set; }
//
//     [JsonProperty("table_name")]
//     public string TableName { get; set; }
//
//     [JsonProperty("initial_time")]
//     public DateTime InitialTime { get; set; }
//
//     [JsonProperty("last_update_time")]
//     public DateTime LastUpdateTime { get; set; }
//
//     public SubscribeChannel(string channelId)
//     {
//         ChannelId = channelId;
//     }
// }
