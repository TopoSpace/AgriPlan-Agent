from agent.deepseek_client import DeepSeekClient

client = DeepSeekClient()

prompt = "我在陕西省有一块地，想种10亩番茄，土壤pH值为6.5，有机质3%。请给出一个科学的种植建议。"

result = client.call_with_function_call(prompt)

print("\n🧠 DeepSeek 智能Agent返回：")
for k, v in result.items():
    print(f"{k}: {v}")
