# local-aetheryte


```
# git clone https://github.com/ff14-advanced-market-search/local-aetheryte.git

cd local-aetheryte
pip install -r requirements.txt
```

Next add in your json data:
- [For wow players](https://github.com/ff14-advanced-market-search/local-aetheryte/blob/main/README.md#wow-setup)
- [For FFXIV players](https://github.com/ff14-advanced-market-search/local-aetheryte/blob/main/README.md#ffxiv-setup)

Last run the python script for whatever alert you want:
- `python ffxiv_pricecheck.py`
- `python ffxiv_undercut.py`
- `python wow_regionpricecheck.py` # for one config and prices on all servers
- `python wow_singlepricecheck.py` # for one config and prices on specific servers
- `python wow_undercut.py`

# FFXIV setup

**Note**: this same setup works for the price alert or undercut options, just do everything here for pricealert instead if you want that

1. Make a list of your webhooks with specific names in the file `ffxiv_user_data/config/undercut/webhooks.json`, a good way to do this is setup different webhooks for different servers
<img width="686" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/9ed5c73a-a80a-4397-82ef-573bc3c26858">
<img width="867" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/30256b28-f91c-4efc-88e2-10694a392c6b">
   
2. Go to the `ffxiv_user_data/undercut/` and make a file that matches the names you put in the webhooks json file.  In each file put your [Undecut data you got from the website](https://saddlebagexchange.com/undercut)

<img width="1140" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/a52fe898-36d0-4129-b120-e2ceb00c286e">

3. Once your data is setup then you can run the `ffxiv_undercut.py` file by right clicking on it in pycharm and then ht run

<img width="495" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/401c0fac-d1f3-4f6d-a0d1-ad0563b3ce51">

4. Then you will get alerts:

<img width="628" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/5f969b10-f438-46e9-a5c6-02bacda659f6">


# WoW setup

Wow does it all in one channel

1. Make a webhook and put it in the file to replace the default example
   
<img width="962" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/cd01532d-29bb-43c5-a7bb-7e0b4d43883f">

2. Get your undercut alert data from the [addon](https://www.curseforge.com/wow/addons/saddlebag-exchange), erase everything in the `wow_user_data/undercut/region_undercut.json` and paste your addon data in:
   
<img width="825" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/012bc5e9-e74e-4a30-a753-9081a1ff6c30">

3.  Rightclick the `wow_undercut.py` and hit run

<img width="491" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/cca1bd89-7ca4-4288-8dc3-c21f58380b0c">
  
4.  get alerts, note we will check once on startup and then again once per hour when the blizzard api data updates

<img width="660" alt="image" src="https://github.com/ff14-advanced-market-search/local-aetheryte/assets/17516896/5de30237-4096-4e82-84b7-49fe2f6feb8c">
