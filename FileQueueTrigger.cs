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
using Microsoft.WindowsAzure.Storage.Blob;
using System.Linq;

namespace HvidevoldDevelopmentENK.GetPixelArt
{
    public static class FileQueueTrigger
    {
        static readonly HttpClient client = new HttpClient();

        [FunctionName("FileQueueTrigger")]
        public static async Task Run(
            [QueueTrigger("filequeue", Connection = "AzureWebJobsStorage")] string filename,
            [Blob("opengameart/{queueTrigger}")] CloudBlockBlob blob,
            [Queue("zipqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> msg,
            [Queue("imgqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> imgs,
            ILogger log)
        {
            log.LogInformation($"C# FileQueueTrigger function processed page {filename}");

            byte[] responseBody = null;

            try	
            {
                responseBody = await Common.ReadURIOrCacheBinary(blob, Common.FileURI + filename, client);

                var isZip = filename.Split('.').Last().ToLower() == "zip";
                var isRar = filename.Split('.').Last().ToLower() == "rar";
                
                if (isZip || isRar) {
                    msg.Add(filename);
                }

                var isJpg = filename.Split('.').Last().ToLower() == "png";
                var isPng = filename.Split('.').Last().ToLower() == "jpg";

                if (isJpg || isPng) {
                    imgs.Add(filename);
                }
            }
            catch(HttpRequestException e)
            {
                log.LogError("\nException Caught!");	
                log.LogError("Message :{0} ",e.Message);
            }
        }
    }
}
