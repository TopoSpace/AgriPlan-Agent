from typing import Dict, Any
from modules.crop_planner import generate_crop_plan
from modules.weather_api import QWeatherClient, load_api_config

# 初始化天气客户端
config = load_api_config()
weather_client = QWeatherClient(apikey=config["apikey"], api_host=config["api_host"])

# ----------------------------- FUNCTION TOOL SCHEMA -----------------------------

CROP_PLAN_FUNCTION = {
    "name": "generate_crop_plan",
    "description": "根据作物类型、地理位置和天气条件生成种植建议",
    "parameters": {
        "type": "object",
        "properties": {
            "crop_type": {
                "type": "string",
                "description": "作物名称，例如：番茄、小麦"
            },
            "location": {
                "type": "string",
                "description": "种植地的经纬度，格式为 '116.41,39.92'"
            },
            "area": {
                "type": "number",
                "description": "土地面积（单位：亩）"
            },
            "soil_info": {
                "type": "object",
                "description": "土壤参数，如 pH、有机质等",
                "properties": {
                    "ph": {"type": "number", "description": "土壤pH值"},
                    "organic_matter": {"type": "number", "description": "土壤有机质百分比"}
                },
                "required": []
            }
        },
        "required": ["crop_type", "location", "area"]
    }
}

WEATHER_FORECAST_FUNCTION = {
    "name": "get_weather_forecast",
    "description": "获取指定经纬度的30天天气预报（用于农业决策）",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "经纬度坐标，格式为 '经度,纬度'，如 '116.41,39.92'"
            }
        },
        "required": ["location"]
    }
}

# ----------------------------- FUNCTION EXECUTORS -----------------------------

def execute_crop_plan_function(arguments: Dict[str, Any]) -> Dict:
    return generate_crop_plan(
        crop_type=arguments["crop_type"],
        location=arguments["location"],
        area=arguments["area"],
        soil_info=arguments.get("soil_info"),
        weather_client=weather_client
    )

def execute_weather_forecast(arguments: Dict[str, Any]) -> Dict:
    return weather_client.get_30day_forecast(arguments["location"])
