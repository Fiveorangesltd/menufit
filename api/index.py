"""
MenuFit API - Vercel Serverless Function
使用 FastAPI + Mangum 适配 Vercel 无服务器环境
MOCK_MODE=true 时无需任何外部依赖即可运行
"""
import json
import os
import uuid
import re
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from mangum import Mangum

# ── 环境配置 ──────────────────────────────────────────────
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

app = FastAPI(title="MenuFit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 数据模型 ──────────────────────────────────────────────
class UserProfile(BaseModel):
    gender: str  # male / female
    age: int
    height: float  # cm
    weight: float  # kg
    goal: str  # 减脂 / 增肌 / 维持
    diet_prefs: Optional[List[str]] = []  # 不吃辣 / 素食 / 清真 等
    activity_level: Optional[str] = "中"  # 低 / 中 / 高
    allergies: Optional[List[str]] = []

class RecommendRequest(BaseModel):
    user_id: str
    mood: Optional[str] = "均衡"  # 更饱 / 更便宜 / 更清淡 / 更好吃

# ── 内存存储（Serverless 无持久化，生产建议接 KV 存储）──────
_profiles: dict = {}
_history: list = []

# ── 工具函数 ──────────────────────────────────────────────
def calculate_bmr(profile: UserProfile) -> float:
    """Mifflin-St Jeor 公式计算基础代谢率"""
    if profile.gender == "male":
        bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
    else:
        bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161
    activity_map = {"低": 1.2, "中": 1.55, "高": 1.725}
    return bmr * activity_map.get(profile.activity_level, 1.55)

def classify_dish(name: str) -> dict:
    """基于关键词对菜品进行分类和风险标注"""
    name_lower = name.lower()
    
    protein_keywords = ["鸡", "鱼", "虾", "牛", "猪", "羊", "蛋", "豆腐", "豆", "肉", "排", "腱", "腿"]
    veggie_keywords = ["菜", "瓜", "笋", "菇", "蘑", "芹", "菠", "白菜", "花椰", "西兰", "生菜", "黄瓜", "番茄", "茄子", "豆角"]
    carb_keywords = ["饭", "面", "粉", "饼", "包", "馒", "粥", "米", "馍", "糕", "饺", "馄饨", "锅贴"]
    fried_keywords = ["炸", "煎", "红烧", "干锅", "爆炒", "油淋", "酥", "锅包"]
    light_keywords = ["蒸", "煮", "白灼", "清炒", "凉拌", "水煮", "炖", "清蒸"]
    spicy_keywords = ["辣", "麻", "椒", "火锅", "川", "湘", "剁椒"]
    
    category = "其他"
    cooking_method = "未知"
    risk_tags = []
    protein_score = 0
    
    for kw in protein_keywords:
        if kw in name:
            category = "蛋白质"
            protein_score = 8
            break
    for kw in veggie_keywords:
        if kw in name:
            category = "蔬菜"
            break
    for kw in carb_keywords:
        if kw in name:
            category = "主食"
            break
    
    for kw in fried_keywords:
        if kw in name:
            cooking_method = "高油"
            risk_tags.append("高油")
            break
    for kw in light_keywords:
        if kw in name:
            cooking_method = "清淡"
            break
    for kw in spicy_keywords:
        if kw in name:
            risk_tags.append("辛辣")
            break
    
    if "糖" in name or "甜" in name or "蜜" in name:
        risk_tags.append("高糖")
    
    return {
        "category": category,
        "cooking_method": cooking_method,
        "risk_tags": risk_tags,
        "protein_score": protein_score
    }

def generate_mock_menu() -> List[str]:
    """返回示例菜单（MOCK模式）"""
    return [
        "白灼虾", "清蒸鲈鱼", "水煮牛肉", "红烧肉", "宫保鸡丁",
        "麻婆豆腐", "炒青菜", "凉拌黄瓜", "番茄炒蛋", "蒜蓉西兰花",
        "米饭", "炒面", "紫菜蛋花汤", "冬瓜排骨汤", "酸辣土豆丝",
        "干煸四季豆", "清炒时蔬", "糖醋里脊", "口水鸡", "蒸蛋羹"
    ]

def build_recommendation(dishes: List[str], profile: UserProfile, mood: str) -> dict:
    """规则引擎：根据用户目标和心情偏好生成推荐"""
    
    # 过滤用户不吃的食物
    filtered = []
    for dish in dishes:
        skip = False
        for pref in (profile.diet_prefs or []):
            if "不吃辣" in pref and any(k in dish for k in ["辣", "麻", "椒"]):
                skip = True
            if "不吃牛肉" in pref and "牛" in dish:
                skip = True
            if "素食" in pref and any(k in dish for k in ["肉", "鸡", "鱼", "虾", "牛", "猪", "羊"]):
                skip = True
        if not skip:
            filtered.append(dish)
    
    if not filtered:
        filtered = dishes[:10]
    
    # 对每道菜打分
    scored = []
    for dish in filtered:
        info = classify_dish(dish)
        score = 0
        
        # 基础分：根据目标
        if profile.goal == "增肌":
            if info["category"] == "蛋白质":
                score += 10
            if info["cooking_method"] == "清淡":
                score += 3
            if "高油" in info["risk_tags"]:
                score -= 3
        elif profile.goal == "减脂":
            if info["category"] == "蔬菜":
                score += 8
            if info["category"] == "蛋白质" and info["cooking_method"] == "清淡":
                score += 7
            if "高油" in info["risk_tags"]:
                score -= 5
            if "高糖" in info["risk_tags"]:
                score -= 5
            if info["category"] == "主食":
                score -= 2
        else:  # 维持
            if info["category"] in ["蛋白质", "蔬菜"]:
                score += 5
            if info["cooking_method"] == "清淡":
                score += 2
        
        # 心情偏好加权
        if mood == "更饱":
            if info["category"] in ["蛋白质", "主食"]:
                score += 4
        elif mood == "更便宜":
            if info["category"] == "蔬菜":
                score += 3
            if info["category"] == "主食":
                score += 2
        elif mood == "更清淡":
            if info["cooking_method"] == "清淡":
                score += 5
            if "高油" in info["risk_tags"]:
                score -= 5
        elif mood == "更好吃":
            if any(k in dish for k in ["红烧", "宫保", "糖醋", "口水", "干锅"]):
                score += 4
        
        scored.append((dish, score, info))
    
    # 排序取前4
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # 确保组合多样性：蛋白质 + 蔬菜 + 可选主食
    selected = []
    has_protein = False
    has_veggie = False
    
    for dish, score, info in scored:
        if len(selected) >= 3:
            break
        if info["category"] == "蛋白质" and not has_protein:
            selected.append((dish, score, info))
            has_protein = True
        elif info["category"] == "蔬菜" and not has_veggie:
            selected.append((dish, score, info))
            has_veggie = True
        elif info["category"] not in ["蛋白质", "蔬菜"]:
            selected.append((dish, score, info))
    
    # 补齐到3道
    for dish, score, info in scored:
        if len(selected) >= 3:
            break
        if (dish, score, info) not in selected:
            selected.append((dish, score, info))
    
    # 生成推荐理由
    recommendations = []
    for dish, score, info in selected:
        reasons = []
        if info["category"] == "蛋白质":
            reasons.append("优质蛋白来源")
        if info["category"] == "蔬菜":
            reasons.append("富含膳食纤维")
        if info["cooking_method"] == "清淡":
            reasons.append("烹饪方式清淡")
        if "高油" in info["risk_tags"]:
            reasons.append("注意：油脂较高")
        if not reasons:
            reasons.append("营养均衡")
        
        recommendations.append({
            "name": dish,
            "reason": "、".join(reasons),
            "category": info["category"]
        })
    
    # 生成下单备注
    notes = []
    has_fried = any("高油" in info["risk_tags"] for _, _, info in selected)
    
    if profile.goal == "减脂":
        notes.append("酱料/汤汁分开放")
        if has_fried:
            notes.append("能换成蒸/煮就不要炸")
        notes.append("主食减半或换杂粮")
        notes.append("少油少盐")
    elif profile.goal == "增肌":
        notes.append("多加青菜/加一份青菜")
        notes.append("不加糖")
        if has_fried:
            notes.append("少油，能蒸煮优先")
    else:
        notes.append("少油少盐")
        notes.append("酱料分开放")
    
    if mood == "更清淡":
        notes.insert(0, "清淡为主，少油少盐")
    
    # 生成替代方案
    alternatives = []
    for dish, score, info in scored[3:6]:
        alternatives.append(dish)
    
    return {
        "recommendations": recommendations,
        "order_notes": notes,
        "alternatives": alternatives,
        "mood": mood,
        "goal": profile.goal
    }

def extract_dishes_with_llm(image_content: bytes, filename: str) -> List[str]:
    """使用 LLM 从图片中提取菜名（非MOCK模式）"""
    if not OPENAI_API_KEY:
        return generate_mock_menu()
    
    try:
        import base64
        from openai import OpenAI
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        image_b64 = base64.b64encode(image_content).decode()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张餐厅菜单图片中的所有菜名，只返回菜名列表，每行一个，不要编号，不要价格，不要描述。如果不是菜单图片，返回'非菜单图片'。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }],
            max_tokens=500
        )
        
        text = response.choices[0].message.content.strip()
        if "非菜单图片" in text:
            return generate_mock_menu()
        
        dishes = [line.strip() for line in text.split("\n") if line.strip()]
        return list(dict.fromkeys(dishes))  # 去重
    except Exception:
        return generate_mock_menu()

# ── API 路由 ──────────────────────────────────────────────

@app.get("/api/healthz")
async def health_check():
    return {
        "status": "ok",
        "mock_mode": MOCK_MODE,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/profile")
async def save_profile(profile: UserProfile):
    user_id = str(uuid.uuid4())[:8]
    _profiles[user_id] = profile.dict()
    tdee = calculate_bmr(profile)
    return {
        "user_id": user_id,
        "tdee": round(tdee),
        "message": "用户资料保存成功"
    }

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    if user_id not in _profiles:
        raise HTTPException(status_code=404, detail="用户资料不存在")
    return _profiles[user_id]

@app.post("/api/analyze-menu")
async def analyze_menu(
    image: UploadFile = File(...),
    user_id: str = Form(...),
    mood: str = Form("均衡")
):
    # 获取用户资料
    if user_id not in _profiles:
        raise HTTPException(status_code=404, detail="请先完成用户资料设置")
    
    profile = UserProfile(**_profiles[user_id])
    
    # 提取菜单
    if MOCK_MODE:
        dishes = generate_mock_menu()
        ocr_source = "mock"
    else:
        image_content = await image.read()
        dishes = extract_dishes_with_llm(image_content, image.filename)
        ocr_source = "llm_vision"
    
    # 生成推荐
    result = build_recommendation(dishes, profile, mood)
    
    # 保存历史
    record = {
        "id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "dishes_count": len(dishes),
        "mood": mood,
        "ocr_source": ocr_source,
        **result
    }
    _history.append(record)
    
    return {
        "dishes": dishes,
        "ocr_source": ocr_source,
        **result,
        "disclaimer": "⚠️ 本推荐仅供参考，非医疗建议。慢性病患者请咨询医生或营养师。"
    }

@app.get("/api/history")
async def get_history(user_id: Optional[str] = None):
    if user_id:
        records = [r for r in _history if r.get("user_id") == user_id]
    else:
        records = _history[-20:]
    return {"history": records, "total": len(records)}

# ── Vercel Serverless 适配 ────────────────────────────────
handler = Mangum(app, lifespan="off")
