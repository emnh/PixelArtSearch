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
    public static class HttpTrigger
    {
        // HttpClient is intended to be instantiated once per application, rather than per-use. See Remarks.
        static readonly HttpClient client = new HttpClient();

        [FunctionName("LoadOpenGameArt")]
        public static async Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", "post", Route = null)] HttpRequest req,
            [Queue("pagequeue"),StorageAccount("AzureWebJobsStorage")] ICollector<string> msg,
            [Blob("opengameart/pages/index.html")] CloudBlockBlob blob,
            ILogger log)
        {
            log.LogInformation("C# HTTP trigger function processed a request.");

            string name = req.Query["name"];

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            dynamic data = JsonConvert.DeserializeObject(requestBody);
            name = name ?? data?.name;

            string responseMessage = string.IsNullOrEmpty(name)
                ? "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response."
                : $"Hello, {name}. This HTTP triggered function executed successfully.";

            // Call asynchronous network methods in a try/catch block to handle exceptions.
            string responseBody = null;
            try	
            {
                //const string uri = "https://opengameart.org/";
                
                // using (TextReader tr = new StreamReader(index)) {
                responseBody = await Common.ReadURIOrCache(blob, Common.SearchURI, client);

                string html = responseBody;
                var htmlDoc = new HtmlDocument();
                htmlDoc.LoadHtml(html);
                var htmlBody = htmlDoc.DocumentNode.SelectSingleNode("//body");
                string page = null;
                foreach (var nNode in htmlBody.Descendants("li"))
                {
                    if (nNode.NodeType == HtmlNodeType.Element && nNode.HasClass("pager-last"))
                    {
                        var aNode = nNode.Element("a");
                        //Console.WriteLine("Node name: " + aNode.Name);
                        //Console.WriteLine(aNode.InnerText);
                        //Console.WriteLine(aNode.Attributes["href"].Value);
                        if (aNode != null) {
                            var href = HttpUtility.HtmlDecode(aNode.Attributes["href"].Value);
                            if (href != null) {
                                Uri myUri = new Uri("https://opengameart.org/" + href);
                                page = HttpUtility.ParseQueryString(myUri.Query).Get("page");
                                log.LogInformation("Last page: " + page);
                            }
                        }
                    }
                }

                int ipage = int.Parse(page);
                //ipage = 1;
                if (page != null && ipage > 0 && ipage < 1000) {
                    for (int i = 0; i <= ipage; i++) {
                        msg.Add(string.Format("{0}", i));
                    }
                }

                //Console.WriteLine(htmlBody.OuterHtml);
            }
            catch(HttpRequestException e)
            {
                Console.WriteLine("\nException Caught!");	
                Console.WriteLine("Message :{0} ",e.Message);
            }
            catch(UriFormatException e) {
                Console.WriteLine("\nException Caught!");
                Console.WriteLine("Message :{0} ",e.Message);
            }

            if (!string.IsNullOrEmpty(name))
            {
                // Add a message to the output collection.
                //msg.Add(string.Format("Name passed to the function: {0}", name));
            }
            
            return 
                responseBody != null ?
                    new ContentResult { Content = responseBody, ContentType = "text/html" } :
                    new ContentResult { Content = responseMessage, ContentType = "text/plain" };
        }
    }
}
