# -*- coding: utf-8 -*-
"""The example demonstrating how to obtain the messages from the agent in a
streaming way."""
import asyncio
import os

from typing import Any
from agentscope.agent import ReActAgent, AgentBase
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import stream_printing_messages
from agentscope.tool import (
    Toolkit,
    execute_shell_command,
    view_text_file,
    execute_python_code,
)

# 创建两个前置回复钩子
def instance_pre_print_hook(
    self: AgentBase,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """修改消息内容的前置回复钩子。"""

    msg = kwargs.get("msg")
    print(msg)

    return kwargs


async def main() -> None:
    """The main function."""
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_shell_command)
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(view_text_file)

    agent = ReActAgent(
        name="Friday",
        sys_prompt="You are a helpful assistant named Friday.",
        # Change the model and formatter together if you want to try other
        # models
        model=DashScopeChatModel(
            api_key=os.environ.get("DASHSCOPE_API_KEY", "sk-aeb7fc8e9d614863b86d3f2c7e0ac70d"),
            model_name="qwen3-vl-plus",
            enable_thinking=False,
            stream=True,
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    agent.register_instance_hook(
        hook_type="pre_print",
        hook_name="test_pre_print",
        hook=instance_pre_print_hook,
    )

    # Prepare a user message
    user_msg = Msg(
        "user",
        "请你写一篇一千字的作文，题目是： 我的父亲！",
        "user",
    )

    agent.set_console_output_enabled(False)

    res = await agent(user_msg)

    print("响应内容：", res.content)
    agent.clear_instance_hooks()

    # We disable the terminal printing to avoid messy outputs
    # agent.set_console_output_enabled(False)
    #
    # # obtain the printing messages from the agent in a streaming way
    # async for msg, last in stream_printing_messages(
    #     agents=[agent],
    #     coroutine_task=agent(user_msg),
    # ):
    #     print(msg, last)



asyncio.run(main())
