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
    public static class FileQueueTrigger
    {
        static readonly HttpClient client = new HttpClient();

        [FunctionName("FileQueueTrigger")]
        public static async Task Run(
            [QueueTrigger("filequeue", Connection = "AzureWebJobsStorage")] string filename,
            [Blob("opengameart/{queueTrigger}")] CloudBlockBlob blob,
            [Queue("zipqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> msg,
            [Queue("sqlqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> sqls,
            ILogger log)
        {
            log.LogInformation($"C# FileQueueTrigger function processed page {filename}");

            try	
            {
                var (responseBody, size) = await Common.ReadURIOrCacheBinary(blob, Common.FileURI + filename, client);

                var isZip = filename.Split('.').Last().ToLower() == "zip";
                var isRar = filename.Split('.').Last().ToLower() == "rar";
                
                if (isZip || isRar) {
                    msg.Add(filename);
                }

                sqls.Add(filename);
                //await Common.AfterUploadFile(filename, size, log, imgs);
            }
            catch(HttpRequestException e)
            {
                log.LogError("\nException Caught!");	
                log.LogError("Message :{0} ",e.Message);
            }
        }
    }
}
