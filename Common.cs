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
    public static class Common
    {
        public static string BaseURI = "https://opengameart.org";
        public static string FileURI = "https://opengameart.org/sites/default";
        public static string SearchURI = "https://opengameart.org/art-search-advanced?keys=&title=&field_art_tags_tid_op=or&field_art_tags_tid=&name=&field_art_type_tid%5B%5D=9&field_art_licenses_tid%5B%5D=17981&field_art_licenses_tid%5B%5D=2&field_art_licenses_tid%5B%5D=17982&field_art_licenses_tid%5B%5D=3&field_art_licenses_tid%5B%5D=6&field_art_licenses_tid%5B%5D=5&field_art_licenses_tid%5B%5D=10310&field_art_licenses_tid%5B%5D=4&field_art_licenses_tid%5B%5D=8&field_art_licenses_tid%5B%5D=7&sort_by=created&sort_order=DESC&items_per_page=144&Collection=";

        public static string ExtractFolder = "/extract";
        public static string Container = "opengameart";
        public static async Task<string> ReadURIOrCache(CloudBlockBlob blob, string uri, HttpClient client)
        {    
            string responseBody = null;

            if (await blob.ExistsAsync())
            {
                responseBody = await blob.DownloadTextAsync();
            }

            if (responseBody == null || responseBody.Length == 0)
            {
                // Avoid spamming server
                await Task.Delay(5000);
                responseBody = await client.GetStringAsync(uri);
                await blob.UploadTextAsync(responseBody);
            }
            
            return responseBody;
        }

        public static async Task<byte[]> ReadURIOrCacheBinary(CloudBlockBlob blob, string uri, HttpClient client, bool needsData = false)
        {    
            //byte[] responseBody;
            MemoryStream ms = new MemoryStream();

            if (await blob.ExistsAsync() && blob.Properties.Length > 0) {
                if (needsData) {
                    await blob.DownloadToStreamAsync(ms);
                }
            }
            else
            {
                // Avoid spamming server
                await Task.Delay(5000);
                await blob.UploadFromStreamAsync(await client.GetStreamAsync(uri));
                if (needsData) {
                    await blob.DownloadToStreamAsync(ms);
                }
            }
            
            return ms.ToArray();
        }
    }
}