from typing import Dict, Any, Callable
from agent.function_calls import (
    CROP_PLAN_FUNCTION,
    execute_crop_plan_function
)

# 注册所有支持的功能函数
REGISTERED_FUNCTIONS: Dict[str, Dict[str, Any]] = {
    "generate_crop_plan": {
        "schema": CROP_PLAN_FUNCTION,
        "handler": execute_crop_plan_function
    }
}


class AgentController:
    def __init__(self):
        self.functions = REGISTERED_FUNCTIONS

    def list_available_functions(self) -> list:
        """
        返回符合 DeepSeek 接口规范的 tools 列表（含 type/function 层）
        """
        return [
            {
                "type": "function",
                "function": f["schema"]  # 把原始函数 schema 包进 function
            }
            for f in self.functions.values()
        ]


    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定函数名称的功能，传入参数
        """
        if function_name not in self.functions:
            return {"error": f"Function `{function_name}` not supported"}

        handler: Callable = self.functions[function_name]["handler"]
        try:
            return handler(arguments)
        except Exception as e:
            return {"error": f"执行函数 `{function_name}` 时出错：{str(e)}"}
