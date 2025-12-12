# -*- coding: utf-8 -*-
"""An example of a conversation with a ReAct agent."""

from agentscope.agents import UserAgent
from agentscope.agents import ReActAgent
from agentscope.message import Msg
from agentscope.service import (
    bing_search,  # or google_search,
    read_text_file,
    write_text_file,
    ServiceToolkit,
    execute_python_code,
)
import agentscope

# Prepare the Bing API key and model configuration
BING_API_KEY = "sk-aeb7fc8e9d614863b86d3f2c7e0ac70d"
s
YOUR_MODEL_CONFIGURATION_NAME = "my_config"
YOUR_MODEL_CONFIGURATION = {
    "model_type": "dashscope_multimodal",
    "config_name": YOUR_MODEL_CONFIGURATION_NAME,
    "model_name": "qwen-vl-max-2025-08-13",
    "api_key": "sk-aeb7fc8e9d614863b86d3f2c7e0ac70d"
    # ...
}

# Prepare the tools for the agent
service_toolkit = ServiceToolkit()

# service_toolkit.add(bing_search, api_key=BING_API_KEY, num_results=3)
# service_toolkit.add(execute_python_code)
# service_toolkit.add(read_text_file)
# service_toolkit.add(write_text_file)

agentscope.init(
    model_configs=YOUR_MODEL_CONFIGURATION,
    project="Conversation with ReActAgent",
)

# Create agents
agent = ReActAgent(
    name="assistant",
    model_config_name=YOUR_MODEL_CONFIGURATION_NAME,
    verbose=True,
    service_toolkit=service_toolkit,
)
# user = UserAgent(name="User", input_hint="User Input ('exit' to quit): ")

res_msg = agent(
    Msg(
        role="user",
        content="解析一下这张图片",
        url="http://183.6.79.229:2640/coesResource/ChatFile/chatRoom-dh111151584291/1753171941684-IMG_20240929_113733.jpg",
        name="user",
    )
)

print(res_msg)

# Build
# x = None
# while True:
#     x = user(x)
#     if x.content == "exit":
#         break
#     x = agent(x)
