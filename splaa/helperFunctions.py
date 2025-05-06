# Author: Claude Petit-Frere
# Date: 11/14/24
# Desc: All the tools are defined here. If you want to add your own try to follow the format of the already existing ones.

import python_weather
import json
import wikipedia
import yfinance as yf
from GoogleNews import GoogleNews
import random
import subprocess
import ollama
from PIL import ImageGrab
import sys
import os
tools = [
  {"type": "function", "function": {"name": "getWeather", "description": "Get the current weather and forecast for a given city", "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "The name of the city for which to get the weather"}}, "required": ["city"]}}},
  {"type": "function", "function": {"name": "wikipediaSearch", "description": "Search for a term/person/anthing on Wikipedia and return a brief summary", "parameters": {"type": "object", "properties": {"term": {"type": "string", "description": "The term to search for on Wikipedia"}}, "required": ["term"]}}},
  {"type": "function", "function": {"name": "getNews", "description": "Get 5 random news article titles from a given topic", "parameters": {"type": "object", "properties": {"topic": {"type": "string", "description": "The topic to get news from (US, World, Business, Technology, Sports, Science, Health)"}},"required": ["topic"]}}},
  {"type": "function", "function": {"name": "getStockPrice", "description": "Get the current stock price of a given ticker symbol", "parameters": {"type": "object", "properties": {"ticker": {"type": "string", "description": "The ticker symbol of the stock to get the price for"}},"required": ["ticker"]}}},
  {"type": "function", "function": {"name": "todoList", "description": "Manage the todo list(if action = read then item = None)", "parameters": {"type": "object", "properties": {"action": {"type": "string", "description": "The action to perform (read, add, remove)"}, "item": {"type": "string", "description": "The item to add or remove"}},"required": ["action", "item"]}}},
]

vision_model = ""

async def getWeather(city):
    string = ''
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        try:
            weather = await client.get(city)
        except:
            return json.dumps(f"Error: Weather for {city} not found")
        string += f"Current Temperature: {weather.temperature}°F"
        
        for daily in weather:
            string += f"\nDate: {daily.date}"
            string += f"Daily Temperature: {daily.temperature}°F"         
            string += "Hourly Forecasts:"
            for hourly in daily:
                string += f"  Time: {hourly.time.strftime('%I:%M %p')}"
                string += f"  Temperature: {hourly.temperature}°F"
                string += f"  Description: {hourly.description}"
                string += f"  Kind: {hourly.kind.name}"
                string += ""
    return json.dumps(string)


async def wikipediaSearch(term):
    term = wikipedia.search(term)
    term = term[0]
    try:
        return json.dumps(f"Summary: {wikipedia.summary(term,auto_suggest=False)}")
    except:
        return json.dumps("Error: Wikipedia search failed")



async def getNews(topic):
    topic_urls = {
        "US": "CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE",
        "World": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB",
        "Business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB",
        "Technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB",
        "Sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlnQVAB",
        "Science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnVHZ0pWVXlnQVAB",
        "Health": "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ"
    }

    if topic not in topic_urls:
        return json.dumps(f"Error: Invalid topic '{topic}'")

    googlenews = GoogleNews()
    googlenews.set_lang('en')
    googlenews.set_topic(topic_urls[topic])
    googlenews.get_news()
    result = googlenews.results()
    texts = random.sample([article['title'] for article in result], min(5, len(result)))
    googlenews.clear()

    return json.dumps(texts)


async def getStockPrice(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return json.dumps(f"Current stock price of {ticker}: {info['currentPrice']}")
    except:
        return json.dumps(f"Error: Unable to get stock price for {ticker}")
    


async def executeCommand(command):
    blacklisted_commands = ["rm", "mkfs", "dd", "shutdown", "reboot", "sudo", "su"]

    for blacklisted_command in blacklisted_commands:
        if blacklisted_command in command:
            return json.dumps(f"Error: Command '{command}' is blacklisted")

    try:
        powershell_command = ["powershell", "-Command", command]
        output = subprocess.check_output(powershell_command, stderr=subprocess.STDOUT).decode("utf-8")
        if output.strip() == "":
            return json.dumps(f"Command '{command}' executed successfully")
        return json.dumps(f"Command output: {output}")
    except subprocess.CalledProcessError as e:
        return json.dumps(f"Error: Command '{command}' failed with exit code {e.returncode}")
    except Exception as e:
        return json.dumps(f"Error: {str(e)}")
       


async def todoList(action, item):
    file_path = "notes.txt"

    if action == "read":
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
                return json.dumps([line.strip() for line in lines])
        except FileNotFoundError:
            return json.dumps("Error: File not found")

    elif action == "add":
        try:
            with open(file_path, "a") as file:
                file.write(item + "\n")
                return json.dumps("Item added successfully")
        except Exception as e:
            return json.dumps(f"Error: {str(e)}")

    elif action == "remove":
        try:
            with open(file_path, "r") as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if line.strip() == item:
                        lines.pop(i)
                        with open(file_path, "w") as file:
                            file.writelines(lines)
                        return json.dumps("Item removed successfully")
                return json.dumps("Error: Item not found")
        except Exception as e:
            return json.dumps(f"Error: {str(e)}")

    else:
        return json.dumps("Error: Invalid action")
    
async def viewScreen():
    image_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = f"{image_dir}/image.png"
    ImageGrab.grab().save(image_path)
    try:
        response = ollama.chat(
            model=vision_model,
            messages=[{
                'role': 'user',
                'content': 'Describe this image and what is in it',
                'images': [image_path]
            }]
        )
        ImageGrab.grab().close()
        return json.dumps(f"Screen Description: {response["message"]["content"]}")      
    except ollama.ResponseError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)


    

available_functions = {
    'getWeather': getWeather,
    'wikipediaSearch': wikipediaSearch,
    'getNews': getNews,
    'getStockPrice': getStockPrice,
    'todoList': todoList
}