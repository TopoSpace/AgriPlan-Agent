import streamlit as st
import time
from agent.deepseek_client import DeepSeekClient
from modules.weather_api import QWeatherClient, load_api_config
from modules.crop_planner import generate_crop_plan
from datetime import datetime
import re
from streamlit_folium import st_folium
import folium

config = load_api_config()
weather_client = QWeatherClient(apikey=config['apikey'], api_host=config['api_host'])
deepseek = DeepSeekClient()

st.set_page_config(page_title="AgriPlan-AI 智能种植助手", page_icon="🌿", layout="wide")
st.title("🌿 AgriPlan-AI Agent 农业智能规划助手")
st.markdown("利用大模型 + 实时地理天气信息 + 用户计划，生成科学、智能的农业种植方案。")
st.divider()

# ========== 阶段一：基础信息 ==========
st.markdown("## 🧩 阶段一：输入地块与土壤信息")
with st.expander("📥 填写基础信息", expanded=True):
    with st.form("input_form"):

        st.markdown("#### 📌 地块基本信息")
        col1, col2 = st.columns(2)
        with col1:
            crop_type = st.text_input("作物类型", value="番茄")
        with col2:
            area = st.number_input("土地面积（亩）", value=10.0, min_value=0.1)

        st.markdown("#### 🌱 土壤信息（可选）")
        ph_col, organic_col = st.columns(2)
        with ph_col:
            ph = st.number_input("pH 值", value=6.5)
        with organic_col:
            organic = st.number_input("有机质含量（%）", value=3.0)

        st.markdown("#### 📍 选择地块位置")
        location_col = st.columns(1)[0]
        with location_col:
            m = folium.Map(location=[34.27, 108.95], zoom_start=5)
            m.add_child(folium.LatLngPopup())
            map_data = st_folium(m, height=350, width=500)
            location = ""
            if map_data and map_data.get("last_clicked"):
                lat = map_data["last_clicked"]["lat"]
                lon = map_data["last_clicked"]["lng"]
                location = f"{lon:.2f},{lat:.2f}"
                st.success(f"✅ 你选择的经纬度：{location}")
            else:
                st.info("请点击地图选点")

        submitted = st.form_submit_button("📤 获取初步建议")


if submitted:
    if location:
        status_box = st.empty()  # 提示占位
        status_box.markdown("🤖 模型正在实时获取地理气象等综合信息...")

        # ⚙️ 后台处理
        soil_info = {"ph": ph, "organic_matter": organic}
        st.session_state["stage1_data"] = {
            "crop_type": crop_type,
            "location": location,
            "area": area,
            "soil_info": soil_info
        }

        result = generate_crop_plan(
            crop_type,
            location,
            area,
            soil_info,
            weather_client
        )

        st.session_state["stage1_result"] = result
        st.session_state["stage1_submitted"] = True

        status_box.success("✅ 模型已将信息综合获取完毕，正在推理建议...")
    else:
        st.warning("📍 请在地图上选择一个位置")

if st.session_state.get("stage1_submitted"):
    stage1 = st.session_state["stage1_data"]
    result = generate_crop_plan(stage1["crop_type"], stage1["location"], stage1["area"], stage1["soil_info"], weather_client)

    st.success("✅ 初步建议生成完毕")
    st.markdown("### 📌 建议摘要")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"- **作物**：{stage1['crop_type']}")
        st.markdown(f"- **面积**：{stage1['area']} 亩")
        st.markdown(f"- **土壤**：pH={stage1['soil_info']['ph']}，有机质={stage1['soil_info']['organic_matter']}%")
    with c2:
        st.markdown("#### ☀️ 未来7天天气摘要")
        st.code(result.get("weather_summary", "N/A"), language="text")

    st.markdown("#### ⚠️ 农业气象风险")
    if result.get("agro_risks"):
        for r in result["agro_risks"]:
            st.warning(r)
    else:
        st.success("暂无明显风险，适宜播种 🌱")

    # === LLM 播种建议流式输出 ===
    st.markdown("#### 🧠 Agent建议")
    weather_summary = result.get("weather_summary", "")
    agro_risks = result.get("agro_risks", [])
    prompt = f"""
你是一名农业种植助手，请根据以下条件给出种植建议：
- 作物：{stage1['crop_type']}
- 面积：{stage1['area']}亩
- 土壤 pH：{stage1['soil_info']['ph']}
- 有机质：{stage1['soil_info']['organic_matter']}%
- 近期天气：{weather_summary}
- 主要气象风险：{'; '.join(agro_risks) if agro_risks else '无'}

请输出适合农户的种植规划建议（包含从种植到收获的全过程，带有日期节点），语气专业但易懂，多用emoji，重点地方需要强调。
"""
    llm_placeholder = st.empty()
    llm_output = ""

    response = deepseek.client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一名农业种植专家"},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    for chunk in response:
        if hasattr(chunk.choices[0].delta, "content"):
            llm_output += chunk.choices[0].delta.content
            llm_placeholder.markdown(llm_output + "▍")

    st.text_area("📋 播种建议全文", llm_output, height=100)

    st.divider()

    # ========== 阶段二 ==========
    st.markdown("## 📅 阶段二：生成逐日农业操作建议")
    with st.expander("🗓️ 填写详细种植计划", expanded=True):
        with st.form("detail_form"):
            col1, col2 = st.columns(2)
            with col1:
                sow_date = st.date_input("预期播种日期", value=datetime.today())
                seed_type = st.text_input("使用苗种", value="鲁番17号")
                irrigation = st.selectbox("灌溉方式", ["滴灌", "喷灌", "漫灌", "自然降水"])
                note = st.text_area("备注", value="无")

            with col2:
                harvest_date = st.date_input("预期收获日期")
                fertilizer = st.text_input("使用肥料", value="磷酸二铵+腐殖酸")
                yield_goal = st.number_input("目标产量（kg/亩）", value=800)

            detailed_submitted = st.form_submit_button("📥 生成逐日操作建议")

    if detailed_submitted:
        with st.spinner("⏳ 正在生成逐日农业操作计划，请稍候..."):
            try:
                forecast30 = weather_client.get_30day_forecast(stage1["location"])
                daily_data = forecast30.get("daily", [])

                if not daily_data:
                    st.error("❌ 获取30天天气失败，无法继续")
                else:
                    st.success(f"✅ 成功获取天气数据（共 {len(daily_data)} 天）")

                    weather_text = "\n".join([
                        f"{d['fxDate']}：{d['textDay']}，{d['tempMin']}~{d['tempMax']}℃，降水{d['precip']}mm"
                        for d in daily_data
                    ])

                    prompt = f"""
你是一名农业种植顾问，请根据以下信息制定每日操作建议：
- 作物：{stage1['crop_type']}
- 面积：{stage1['area']}亩
- 苗种：{seed_type}
- 肥料：{fertilizer}
- 灌溉方式：{irrigation}
- 播种：{sow_date}
- 收获：{harvest_date}
- 目标产量：{yield_goal}kg/亩
- 备注：{note}

以下是未来30天天气（每天简要）：
{weather_text}

请以播种日起开始，按每天列出农事操作建议，输出形式（模仿卡片式日历，多用emoji，需要直观清晰并且美观）：日期+天气摘要：操作事项（重要事项需强调）
"""

                    # === 第二阶段流式生成输出 ===
                    daily_placeholder = st.empty()
                    daily_output = ""

                    response = deepseek.client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "你是农业助手"},
                            {"role": "user", "content": prompt}
                        ],
                        stream=True
                    )

                    for chunk in response:
                        if hasattr(chunk.choices[0].delta, "content"):
                            daily_output += chunk.choices[0].delta.content
                            daily_placeholder.markdown(daily_output + "▍")

                    st.success("✅ 农事操作计划生成完毕")
                    st.text_area("📋 农事操作全文", daily_output, height=100)

            except Exception as e:
                st.error(f"❌ 生成失败：{str(e)}")
else:
    st.info("📌 请先填写并提交【阶段一】信息，方可进行阶段二操作。")
