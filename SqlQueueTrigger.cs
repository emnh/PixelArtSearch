using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using System.Net.Http;
using Newtonsoft.Json;
using HtmlAgilityPack;
using System.Web;
using Microsoft.Azure.Storage.Blob;
using System.Linq;

namespace HvidevoldDevelopmentENK.GetPixelArt
{
    public static class SqlQueueTrigger
    {
        [FunctionName("SqlQueueTrigger")]
        public static async Task Run(
            [QueueTrigger("sqlqueue", Connection = "AzureWebJobsStorage")] string myQueueItem,
            [Blob("opengameart/{queueTrigger}")] CloudBlockBlob blob,
            [Queue("imgqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> imgs,
            ILogger log)
        {
            log.LogInformation($"C# SqlQueueTrigger function processed: {myQueueItem}");

            if (await blob.ExistsAsync() && blob.Properties.Length > 0) {
                await Common.AfterUploadFile(myQueueItem, blob.Properties.Length, log, imgs);
            }
        }
    }
}
