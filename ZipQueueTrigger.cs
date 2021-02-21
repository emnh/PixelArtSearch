using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.WindowsAzure.Storage;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Logging;
using System.Net.Http;
using Newtonsoft.Json;
using HtmlAgilityPack;
using System.Web;
using Microsoft.WindowsAzure.Storage.Blob;
using System.Collections.Generic;
using System.Linq;
using SharpCompress.Archives;
using SharpCompress.Archives.Zip;
using SharpCompress.Archives.Rar;
using SharpCompress.Common;
using SharpCompress.Readers;
using System.Text;

namespace HvidevoldDevelopmentENK.GetPixelArt
{
    
    public static class ZipQueueTrigger
    {
        public static async Task Extract(IEnumerable<IArchiveEntry> archiveEntries, string zipfile, CloudBlobContainer container, ILogger log, ICollector<string> imgs) {                    
            string lastOutBlobName = Common.ExtractFolder + zipfile + "/" + HttpUtility.UrlEncode(archiveEntries.Last().Key, Encoding.UTF8);
            var lastOutBlob = container.GetBlockBlobReference(lastOutBlobName);
            if (await lastOutBlob.ExistsAsync() && lastOutBlob.Properties.Length == archiveEntries.Last().Size) {
                log.LogInformation($"Last file {lastOutBlobName} already exists, so skipped ALL.");
            } else {
                foreach (var archiveEntry in archiveEntries.Where(entry => !entry.IsDirectory))
                {
                    log.LogInformation($"Now processing {archiveEntry.Key}");

                    string outBlobName = Common.ExtractFolder + zipfile + "/" + HttpUtility.UrlEncode(archiveEntry.Key, Encoding.UTF8);

                    log.LogInformation($"Writing blob {outBlobName}");

                    NameValidator.ValidateBlobName(outBlobName);

                    var blockBlob = container.GetBlockBlobReference(outBlobName);
                    if (await blockBlob.ExistsAsync() && blockBlob.Properties.Length == archiveEntry.Size) {
                        log.LogInformation($"{outBlobName} already exists, so skipped.");
                    } else {
                        await using var fileStream = archiveEntry.OpenEntryStream();
                        await blockBlob.UploadFromStreamAsync(fileStream);
            
                        var isJpg = outBlobName.Split('.').Last().ToLower() == "png";
                        var isPng = outBlobName.Split('.').Last().ToLower() == "jpg";

                        if (isJpg || isPng) {
                            imgs.Add(outBlobName);
                        }
                        
                        log.LogInformation($"{outBlobName} processed successfully and moved to destination container.");
                    }
                }
            }
        }
    
        [FunctionName("ZipQueueTrigger")]
        public static async Task Run([
            QueueTrigger("zipqueue", Connection = "AzureWebJobsStorage")] string zipfile,
            [Blob("opengameart/{queueTrigger}")] CloudBlockBlob blob,
            [StorageAccount("AzureWebJobsStorage")] CloudStorageAccount storageAccount,
            [Queue("imgqueue"), StorageAccount("AzureWebJobsStorage")] ICollector<string> imgs,
            ILogger log)
        {
            log.LogInformation($"C# ZipQueueTrigger function processed: {zipfile}");

            var isZip = zipfile.Split('.').Last().ToLower() == "zip";
            var isRar = zipfile.Split('.').Last().ToLower() == "rar";

            try{
                if(isZip || isRar){

                    CloudBlobClient blobClient = storageAccount.CreateCloudBlobClient();

                    CloudBlobContainer container = blobClient.GetContainerReference(Common.Container);
                    await container.CreateIfNotExistsAsync();
                    
                    using(MemoryStream blobMemStream = new MemoryStream()){

                        await blob.DownloadToStreamAsync(blobMemStream);

                        var zipReaderOptions = new ReaderOptions()
                        {
                            ArchiveEncoding = new ArchiveEncoding(Encoding.UTF8, Encoding.UTF8), LookForHeader = true
                        };

                        log.LogInformation("Blob is a zip/rar file; beginning extraction....");
                        blobMemStream.Position = 0;

                        if (isZip) {
                            using (var reader = ZipArchive.Open(blobMemStream, zipReaderOptions)) {
                                await Extract(reader.Entries, zipfile, container, log, imgs);
                            }
                        } else if (isRar) {
                            using (var reader = RarArchive.Open(blobMemStream, zipReaderOptions)) {
                                await Extract(reader.Entries, zipfile, container, log, imgs);
                            }
                        }
                    }
                }
            }
            catch(Exception ex){
                log.LogError($"Error! Something went wrong: {ex.Message}");
            }            
        }
    }
}
