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
using System.Collections.Generic;

namespace HvidevoldDevelopmentENK.GetPixelArt
{
    public static class PageQueueTrigger
    {
        static readonly HttpClient client = new HttpClient();

        [FunctionName("PageQueueTrigger")]
        public static async Task Run(
            [QueueTrigger("pagequeue", Connection = "AzureWebJobsStorage")] string page,
            [Blob("opengameart/pages/page{queueTrigger}.html")] CloudBlockBlob blob,
            [Queue("contentqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> msg,
            ILogger log)
        {
            log.LogInformation($"C# PageQueueTrigger function processed page {page}");

            string responseBody = null;

            try	
            {
                responseBody = await Common.ReadURIOrCache(blob, Common.SearchURI + "&page=" + page, client);

                var htmlDoc = new HtmlDocument();
                htmlDoc.LoadHtml(responseBody);
                var htmlBody = htmlDoc.DocumentNode.SelectSingleNode("//body");

                var hashSet = new HashSet<string>();
                
                foreach (var nNode in htmlBody.Descendants("a"))
                {
                    if (nNode.NodeType == HtmlNodeType.Element && nNode.Attributes["href"] != null && nNode.Attributes["href"].Value.StartsWith("/content/"))
                    {
                        hashSet.Add(HttpUtility.HtmlDecode(nNode.Attributes["href"].Value));
                    }
                }
                foreach (var urlPart in hashSet) {
                    msg.Add(urlPart);
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
