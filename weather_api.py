import requests
import yaml
from typing import Dict, Any, List

# 从 config 文件中读取 API Key 配置
def load_api_config(config_path="config/api_keys.yaml") -> Dict[str, str]:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['qweather']


class QWeatherClient:
    def __init__(self, apikey: str, api_host: str):
        self.apikey = apikey
        self.api_host = api_host

    def get_current_weather(self, location: str) -> Dict[str, Any]:
        url = f"{self.api_host}/v7/weather/now"
        params = {
            "location": location,
            "key": self.apikey,
            "unit": "m",
            "lang": "zh"
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_7day_forecast(self, location: str) -> Dict[str, Any]:
        url = f"{self.api_host}/v7/weather/7d"
        params = {
            "location": location,
            "key": self.apikey,
            "unit": "m",
            "lang": "zh"
        }
        response = requests.get(url, params=params)
        return response.json()

    def get_30day_forecast(self, location: str) -> Dict[str, Any]:
        url = f"{self.api_host}/v7/weather/30d"
        params = {
            "location": location,
            "key": self.apikey,
            "unit": "m",
            "lang": "zh"
        }
        response = requests.get(url, params=params)
        return response.json()

    def extract_weather_risks(self, forecast_json: Dict[str, Any]) -> List[str]:
        """从7天天气预报中提取农业风险事件提示（暴雨、霜冻等）"""
        warnings = []
        for day in forecast_json.get("daily", []):
            date = day["fxDate"]
            temp_min = int(day["tempMin"])
            precip = float(day["precip"])
            text_day = day["textDay"]

            if temp_min < 5:
                warnings.append(f"{date}: 🌡️ 低温预警，最低{temp_min}℃，可能不适宜播种")
            if precip > 10:
                warnings.append(f"{date}: 🌧️ 强降雨预警，预计降水{precip}mm，建议避免播种")
            if "雷" in text_day or "雨" in text_day:
                warnings.append(f"{date}: ⛈️ 白天天气为'{text_day}'，可能影响农事操作")

        return warnings
