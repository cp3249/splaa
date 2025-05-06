# Author: Claude Petit-Frere
# Date: 11/14/24
# Desc: This is where the main logic for the ollama inference is stored

from ollama import chat
from .audioFunctions import generateAudio, recordAudio, whisperTranscription
from . import helperFunctions
import ollama
import sys

async def generateResponse(model, assistant_name, user_name, speaker_file, system_prompt, command_permission, enable_vision, vision_model):
    
    if command_permission:
        helperFunctions.tools.append({"type": "function", "function": {"name": "executeCommand", "description": "Executes a command in the powershell terminal. eg start firefox, systeminfo ...ect", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "The command to execute"}},"required": ["command"]}}})
        helperFunctions.available_functions['executeCommand'] = helperFunctions.executeCommand
    
    if enable_vision:
        try:
            ollama.pull(vision_model)
            if "projector_info" not in ollama.show(vision_model):
                print(f"Error: {vision_model} model does not support vision")
                sys.exit(1)
        except ollama.ResponseError:
            print(f"Error: Model {vision_model} does not exist.")
            sys.exit(1)
        helperFunctions.vision_model = vision_model
        helperFunctions.tools.append({"type": "function", "function": {"name": "viewScreen", "description": "Get a detailed description of the current screen/what the user sees. Use anytime an image is needed for info.", "parameters": {"type": "object", "properties": {},"required": []}}})
        helperFunctions.available_functions['viewScreen'] = helperFunctions.viewScreen


    history = [
    {'role': 'system', 'content': f"Rule: all outputs should be concise, english and in paragraph form. Your Name:{assistant_name}. Prompt: {system_prompt}. User Name:{user_name}."}
    ]

    try:
        ollama.pull(model)
    except ollama.ResponseError:
        print(f"Error: Model {model} does not exist.")
        sys.exit(1)
    except Exception:
        print("Error: Ollama process not detected. \nPlease make sure you have Ollama installed and currently running.")
        sys.exit(1)
        
    try:
        response = chat(model, messages=history, tools=helperFunctions.tools)
    except ollama.ResponseError as e:
        print(e)
        sys.exit(1)

    while True:
        user_text = whisperTranscription(recordAudio())
        if assistant_name.lower() in user_text.lower():
            history.append({'role': 'user', 'content': f'/no_think {user_text}'})
            response = chat(model, messages=history, tools=helperFunctions.tools)
            if response['message'].get('tool_calls'):
                for tool in response['message']['tool_calls']:
                    print(f"Using {tool['function']['name']} tool")
                    function_to_call = helperFunctions.available_functions[tool['function']['name']]
                    function_response = await function_to_call(**tool['function']['arguments'])
                    history.append({'role': 'tool','content': function_response,})
                response = chat(model, messages=history, tools=helperFunctions.tools)
            generateAudio(response['message']['content'], speaker_file)
            print(f"Response: {response['message']['content']}")
            print("------------------", end="\n")
            history.append(response['message'])