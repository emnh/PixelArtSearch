/*
using System;
using System.IO;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Host;
using Microsoft.Extensions.Logging;
using System.Linq;

namespace HvidevoldDevelopmentENK.GetPixelArt
{
    public static class ImageBlobTrigger
    {
        [FunctionName("ImageBlobTrigger")]
        public static void Run(
            [BlobTrigger("opengameart/{name}", Connection = "AzureWebJobsStorage")] Stream myBlob,
            string name,
            [Queue("imgqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> msg,
            ILogger log)
        {
            log.LogInformation($"C# ImageBlobTrigger function Processed blob\n Name:{name} \n Size: {myBlob.Length} Bytes");

            var isJpg = name.Split('.').Last().ToLower() == "png";
            var isPng = name.Split('.').Last().ToLower() == "jpg";

            if (isJpg || isPng) {
                msg.Add(name);
            }
        }
    }
}
*/