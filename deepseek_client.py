from openai import OpenAI
import json
from typing import Dict, Any
from agent.agent_controller import AgentController


class DeepSeekClient:
    def __init__(self,
                 api_key: str = "replace your api key here",
                 base_url: str = "https://api.deepseek.com/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.controller = AgentController()

    def call_with_function_call(self, user_prompt: str, model: str = "deepseek-chat") -> Dict[str, Any]:
        tools = self.controller.list_available_functions()

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个农业专家助手，可以为用户制定种植计划。"},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools,
            tool_choice="auto"
        )

        return self._handle_response(response)

    def _handle_response(self, response: Any) -> Dict[str, Any]:
        choice = response.choices[0]

        # 如果触发了函数调用
        if choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"🎯 触发函数: {function_name}")
            print(f"📦 参数: {arguments}")

            result = self.controller.execute(function_name, arguments)
            return result

        # 否则返回普通文本
        return {"text": choice.message.content}
