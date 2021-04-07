# Pixel Art Reverse Image Search for OpenGameArt

# Why did I want a reverse image search for OpenGameArt?
I wanted to build a reverse image search for OpenGameArt as Google Image Search and TinEye don't give good results for it.
I had previously generated a [huge tile map](https://opengameart.org/content/all-of-2d-art-on-opengameart-in-1-sprite-sheet) to give an overview of similar images on OpenGameArt, but it wasn't very resource friendly on the web or image browser and had to be split into smaller files, plus it's not searchable in any way, just scrollable.
So I wanted a way for people to explore what kind of art is available on OpenGameArt, and landed on using similarity search to browse the image space.

# How did I do the crawling?
The first thing I had to do was retrieve the search results for the query I was interested in on OpenGameArt, mostly the 2D art.
Then I had to retrieve each HTML page which was in the search results index and parse the HTML for links to files.
OpenGameArt contains a lot of archive files like zip and rar files, so I then had to unpack them to get to the images.

# Which technology did I use for the crawling and how much did it cost?
I used Azure Functions to do the crawling steps, with some back and forth manual intervention to correct things as needed.
Each step had its own queue and then put the job for the next step on the next queue.
In the end the invocations cost around 50 USD on Azure, for let's say 10-20 million Function invocations if I remember correctly.

# Which alternatives did I investigate?
I tried to use the open source Milvus database, but it crashed on my DigitalOcean server because I didn't have enough memory on it.
Then I accidentally and luckily discovered the link to [Pinecone](https://www.pinecone.io/) in a Hacker News comment section and decided to use that instead, as the trial was free and I didn't have to expand my server memory to use Milvus.
In the end I expanded my server anyway, but I didn't try Milvus again (at least not yet).

# What data do you need on each image to create a reverse image search?
I used [VGG16 feature extraction](https://towardsdatascience.com/extract-features-visualize-filters-and-feature-maps-in-vgg16-and-vgg19-cnn-models-d2da6333edd0) in [my script for this](https://github.com/emnh/PixelArtSearch/blob/master/scripts/featureVectors.py).
See the article for more information, but in essence it's 4096 32-bit floating point numbers for each image, which describe various features of the image, say for instance in a very simplified way how many stripes or squares it has or how green it is.
But these features are based on neurons in the neural network for VGG16 (which is usually used for image classification), so the features could be more complicated than what is described by simple feature tags.
And the reason we need these vectors is that it's easy to use Euclidean distance or cosine similarity or another measure on two vectors to see if they are similar, and then consequently the images are similar.
Furthermore there is search technology on these vectors that enable quick search on a large amount of them.

# How did I maintain a link between the image URLs and the vector datebase feature vectors?
I also wanted to put all the image URLs into a SQL database in the end, and have a flag for whether I had made the VGG16 feature extraction and whether it was added to the vector database (Milvus or [Pinecone](https://www.pinecone.io/).
It's essential to be able to map back and forth between an integer primary key, which is used in [Pineone](https://www.pinecone.io/), and the URL and perhaps other metadata that belongs to the image, as [Pinecone](https://www.pinecone.io/ doesn't store other metadata than the primary key.

# How long time did it take?
I think I spent a week in total to run all the code to finish, each step taking on the order of a day or two, crawl, computing feature vectors.
I don't remember how much time it took to insert the vectors into the [Pinecone](https://www.pinecone.io/) database, but I think it was not the most time-consuming step.

# What does the final search look like?
The final search with an example can be found [here](https://emh.lart.no/ogasearch/?imsi=monster%20stone%20soup&count=20).
There are two ways of searching, either you can put a keyword, which just plainly (and a bit slowly at O(n)) iterates linearly through the URLs looking for a match.
I stuck with linear search since it's simple to implement and all the URLs are kept in memory anyway so it's not that slow.
It looks like this: ![OpenGameArt Search](https://emh.lart.no/ogasearch/demo.jpg)

# What are some problems in encountered?
At the end I also added a quick fix to remove near-duplicate image results which had an identical score.
I ran into some troubles on the search page with "double" URL encoding, because I had stored the files using URL encoding in the file system, but I worked around it with some detection code on the frontend for when the browser double-encoded the URL-encoded file names.
I recommend storing the crawled files without URL encoding.
I regret that my scripts are not so high quality or polished, for example there are multiple steps in scripts and I change things by editing the script instead of taking command line arguments.
I don't feel like posting snippets from the scripts and explaining as they are a bit messy.
Additionally I moved the files from Azure storage to my DigitalOcean server mid-way, before processing the feature extraction, so there's some inconsistent data location handling.

# What are the final takeaways?
I recommend doing the crawl perhaps on a cheaper substrate than Azure Functions and Azure Storage to save some money, for example your own server or a fixed price Cloud server.
Well it just cost 50 USD but I could have done it for free on my DigitalOcean server, so that's why.
I recommend building a more robust crawler, idempotent and restartable at any point which it may terminate at or require some manual intervention (for example I exceeded the Azure Function maximum run time of 5 minutes on extracting some of the large zip files, so I extracted them running the Functions locally in VS Code).
One thing I regret that I didn't get done this time was to extract all the tiles from tile sheets to individual images for searching. That would have made the search even more useful. On the other hand it could have cluttered the similarity search with too many nearly identical images.

# Conclusion and final remarks
It might also be useful to prototype the system using a bit of content, then run the whole pipeline end to end on all the content once you get it working, instead of completing the first step in crawl, then doing all feature extraction and then doing all database insertion as I did.
In conclusion what I made was a bit of a hack, not so robust scripting for updating for new content, but it worked fine as a prototype and gave decent image search results (not always so spot on, but I blame it on that the feature extraction is not really targeted at tiny pixel art (though resized/upscaled before feature extraction)).
It could be interesting to see whether Milvus could also deliver similar results, a side by side comparison of some kind, on speed and quality, but I found it much easier to use [Pinecone](https://www.pinecone.io/) since it's already up and running as a service so that I didn't have to run my own vector database.

# Script Locations

 - Azure OpenGameArt crawler in \*.cs files. Moved to DigitalOcean later on because of pricing.
 - Scripts for machine learning and pinecone.io query server in /scripts.
 - /index.html is front page.
 - See also https://github.com/emnh/opengameart/ .
