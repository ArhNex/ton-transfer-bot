# ton-transfer-bot

## Description

This is a bot that allows you to receive and transfer ton from one wallet to another while saving transactions in the database.

## How to run

Download the project, install all necessary dependencies using the `pip3 install -r requirements` command in the `source` folder. 

### For start bot

1. Create an .env in the bot folder with the following fields.
	``` 
    BOT_TOKEN= private key of telegram bot
    BOT_NICKNAME = bot name
    PUBLIC_LINK = link to database like http://127.0.0.1/
    KEY = key which should be the same as in WebDB
	```
2. Run `python3 bot.py`

### For start WebDB

1. Create an .env in the bot folder with the following fields.
	``` 
    TOKEN= private key
	```
1. Run `uvicorn db_api:app`
    