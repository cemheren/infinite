# infinite
OSXFuse interface for Azure blob storage. Allows extending your Mac OS storage infinitely into cloud.

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
3. For learning FUSE which is cool. 

# how
Fill-in your Azure storage credentials in the beginning of creds.json. 
Create mount and cache folders whereever in your filesystem. Run the azurefiles.py with mount and cache folder arguments. 
> mkdir mount 

> mkdir cache

> sudo python3 azurefiles.py cache mount

# is it stable? 
Somewhat. I wouldn't try it on anything you won't be ok with losing.  

# screenshots
Sample blob I've been experimenting on, supports somewhat harder scenarios such as preview. 

<img src="https://github.com/cemheren/infinite/blob/master/screenshots/Screenshot%202018-10-20%2020.44.41.png" width="700">

# notes
This project is not affiliated with Microsoft or Azure. It's by any means not supported officially.
