# infinite
OSXFuse interface for Azure blob storage. Allows extending your Mac storage infinitely into cloud.

# dependencies
fusepy
> pip install fusepy

azure storage python libraries
https://github.com/Azure/azure-storage-python
> pip install azure
> pip install azure-storage-blob

You also need to create an Azure storage account on https://portal.azure.com. I don't bother supporting s3 because Azure storage is significantly cheaper. 

FUSE for Mac OS
https://osxfuse.github.io/
Download the latest release. 

# why
1. For moving files to the cloud seamlessly. I mainly use these files for training ML models on cloud. 
2. Dropbox is expensive :(. I want a place to store my files longer term. With Azure storage archive tier 100GB data costs < 0.2$ per month. 
3. Learning FUSE. 

# notes
This project is not affiliated with Microsoft or Azure. It's by any means not supported officially.
