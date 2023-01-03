import requests
from bs4 import BeautifulSoup
from lxml import etree as et
import sys
import boto3
import json

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
    'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
}

def get_amazon_price(dom):
    item_price = dom.xpath('//span[@class="a-offscreen"]/text()')[0]
    item_price = item_price.replace('$', '')
    return float(item_price)

def get_product_name(dom):
    name = dom.xpath('//span[@id="productTitle"]/text()')
    [name.strip() for name in name]
    return name[0]

def get_master_price(url):
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
         response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
         data.extend(response['Items'])
    for i in data:
        if i['url'] == i['url']:
            return float(i['product_price'])
     
def get_dynamo_urls():
    url_list = []
    boto3.setup_default_session(profile_name="default")
    table_name = "WishList"
    dynamodb_resource = boto3.resource("dynamodb")
    table = dynamodb_resource.Table(table_name)
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
         response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
         data.extend(response['Items'])
    for i in data:
        url_list.append(i['url'])
    return url_list

price_drop_products = []
price_drop_list_url = []

for product_url in get_dynamo_urls():

    response = requests.get(product_url, headers=header)
    soup = BeautifulSoup(response.content, 'html.parser')
    main_dom = et.HTML(str(soup))

    price = get_amazon_price(main_dom)
    product_name = get_product_name(main_dom)
    
    boto3.setup_default_session(profile_name="default")
    table_name = "WishList"
    dynamodb_resource = boto3.resource("dynamodb")
    table = dynamodb_resource.Table(table_name)
    
    if price < get_master_price(product_url):
        change_percentage = round((get_master_price(product_url) - price) * 100 / get_master_price(product_url))

        if change_percentage > 10:
            print(' There is a {}'.format(change_percentage), '% drop in price for {}'.format(product_name))
            print('Click here to purchase {}'.format(product_url))
            price_drop_products.append(product_name)
            price_drop_list_url.append(product_url)

if len(price_drop_products) == 0:
    sys.exit('No Price drop found')

message = "There is a drop in price for {}".format(len(price_drop_products)) + " products." + "Click to purchase"

for items in price_drop_list_url:
    message = message + "\n" + items

arn = 'SNS_ARN'
sns_client = boto3.client('sns')

sns_client.publish(TopicArn=arn, Message=message, Subject='PriceDropAlert')
