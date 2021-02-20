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

namespace HvidevoldDevelopmentENK.GetPixelArt
{
    public static class ContentQueueTrigger
    {
        static readonly HttpClient client = new HttpClient();

        [FunctionName("ContentQueueTrigger")]
        public static async Task Run(
            [QueueTrigger("contentqueue", Connection = "AzureWebJobsStorage")] string page,
            [Blob("opengameart/{queueTrigger}.html")] CloudBlockBlob blob,
            [Queue("filequeue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> msg,
            ILogger log)
        {
            log.LogInformation($"C# ContentQueueTrigger function processed page {page}");

            string responseBody = null;

            try	
            {
                responseBody = await Common.ReadURIOrCache(blob, Common.BaseURI + page, client);

                var htmlDoc = new HtmlDocument();
                htmlDoc.LoadHtml(responseBody);
                var htmlBody = htmlDoc.DocumentNode.SelectSingleNode("//body");
                
                foreach (var nNode in htmlBody.Descendants("a"))
                {
                    if (nNode.NodeType == HtmlNodeType.Element &&
                        nNode.Attributes["href"] != null &&
                        nNode.Attributes["href"].Value.Contains("/default/files/"))
                    {
                        msg.Add(HttpUtility.HtmlDecode(nNode.Attributes["href"].Value.Replace(Common.FileURI, "")));
                    }
                }
            }
            catch(HttpRequestException e)
            {
                log.LogError("\nException Caught!");	
                log.LogError("Message :{0} ",e.Message);
                log.LogError("Stack :{0}", e.StackTrace.ToString());
            }
            catch (NullReferenceException e) {
                log.LogError("\nException Caught!");	
                log.LogError("Message :{0} ", e.Message);
                log.LogError("Stack :{0}", e.StackTrace.ToString());
            }
        }
    }
}
