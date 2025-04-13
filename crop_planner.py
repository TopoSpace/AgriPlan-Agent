from typing import Dict, Optional
from modules.weather_api import QWeatherClient
from openai import OpenAI
import os

# 创建 LLM 接口（使用 DeepSeek-V3）

client = OpenAI(api_key="replace your api key here", base_url="https://api.deepseek.com/v1")
>>>>>>> 90fdf04 (Initial commit - upload AgriPlan-AI project)

def generate_crop_plan(
    crop_type: str,
    location: str,
    area: float,
    soil_info: Optional[Dict[str, float]],
    weather_client: QWeatherClient
) -> Dict:

    # Step 1: 获取天气数据
    forecast = weather_client.get_7day_forecast(location)
    warnings = weather_client.extract_weather_risks(forecast)

    # Step 2: 构建 prompt 给大模型生成建议
    weather_summary = "\n".join([
        f"{d['fxDate']}: {d['textDay']}，温度{d['tempMin']}~{d['tempMax']}℃"
        for d in forecast["daily"]
    ])

    soil_desc = f"土壤pH={soil_info.get('ph')}，有机质={soil_info.get('organic_matter')}%" if soil_info else "无土壤信息"
    prompt = (
        f"你是一位农业专家，请根据以下信息制定详细的种植建议：\n"
        f"- 作物类型：{crop_type}\n"
        f"- 土地面积：{area}亩\n"
        f"- 土壤条件：{soil_desc}\n"
        f"- 未来7天天气：\n{weather_summary}\n\n"
        f"请给出：1）推荐播种日期；2）施肥计划；3）预计生育周期；4）注意事项；5）农事建议"
    )

    # Step 3: 调用大模型生成文本建议
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一名智慧农业顾问"},
            {"role": "user", "content": prompt}
        ]
    )

    suggestion = response.choices[0].message.content

    return {
        "crop": crop_type,
        "location": location,
        "area": area,
        "soil_info": soil_info or "未提供",
        "weather_summary": weather_summary,
        "agro_risks": warnings,
        "llm_suggestion": suggestion
    }
