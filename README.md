# sobble-bot-public
## /auction [seconds] [min_bid]* [description]*
Starts an auction where anyone has [seconds] seconds to place a bid before the auction ends
After the auction starts, channel members may enter a number to bid that amount or a period to bid the minimum amount
The new minimum bid is 5% greater than the current bid, rounded up to the nearest integer
Bids may not be placed for one second after the last one

##### Seconds
Specifies the number of seconds from the last bid before the auction ends
##### Min_bid (optional)
First bid must be at least this
##### Description (optional)
Item description, will be displayed at start and end of auction

## /commands
Get a link to a google doc with this page

## /resetspreadsheet
Reset the price lookup spreadsheet

## /spreadsheet
Uses /tcgp (if not japanese) or /tcgr (if japanese) on the spreadsheet inputs and generates outputs
Pings user when done
Yellow highlight indicates there was more than one result returned, you should manually check to see if the card returned was the right one
You need to make your own spreadsheet and credentials file using Google's API for the spreadsheet commands to work

## /tcgp [search] [keywords]*
Returns the first few results of looking up [search] in tcgplayer

##### Search	
What is inputted into the search bar of tcgplayer
##### Keywords (optional)
Returns only the results with keywords in its name
Can put multiple comma separated words

* Ex: /tcgp [search: kiryu coco sp]
Returns both trial deck and booster sp
* Ex: /tcgp [search: coco sp] [keywords: sp, autumn]
Search result must have “sp” and “autumn” in it to be returned
Returns trial deck sp (Kiryu Coco, Autumn Path (SP))

## /tcgr [search] [keywords]* [category]*
Returns the first few results of looking up [search] in tcgrepublic

##### Search
What is put into the search bar of tcgrepublic
##### Keywords (optional)
Returns only the results with keywords in its name
Can put multiple comma separated words
##### Category (optional)
Specifies a category to look under
Only categories supported are: pokemon, weiss


* Ex: /tcgp [search: nino sp]
Returns 5 results from Weiss Schwarz and Precious Memories
* Ex: /tcgp [search: nino sp] [keywords: bath]
Search result must have “bath” in it to be returned
Returns Nino Nakano, After Bath 5HY/W83-107SP SP Foil
* Ex: /tcgp [search: nino sp] [keywords: sp, bath] [category: weiss]
Search result must have “sp” and “bath” as well as be in the Weiss category to be returned
Returns Nino Nakano, After Bath 5HY/W83-107SP SP Foil

