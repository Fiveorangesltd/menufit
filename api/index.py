"""
MenuFit API - Vercel Serverless Function (原生 Python Handler)
使用 Vercel 原生 http.BaseHTTPRequestHandler 格式
MOCK_MODE=true 时无需任何外部依赖即可运行
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import uuid


from datetime import datetime

# ── 环境配置 ──────────────────────────────────────────────
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# ── 内存存储（Serverless 每次冷启动重置，生产建议接 KV 存储）──
_profiles: dict = {}
_history: list = []

# ── 工具函数 ──────────────────────────────────────────────
def calculate_bmr(profile: dict) -> float:
    """Mifflin-St Jeor 公式计算基础代谢率"""
    w = profile.get("weight", 65)
    h = profile.get("height", 170)
    a = profile.get("age", 25)
    g = profile.get("gender", "male")
    if g == "male":
        bmr = 10 * w + 6.25 * h - 5 * a + 5
    else:
        bmr = 10 * w + 6.25 * h - 5 * a - 161
    activity_map = {"低": 1.2, "中": 1.55, "高": 1.725}
    level = profile.get("activity_level", "中")
    return bmr * activity_map.get(level, 1.55)

def classify_dish(name: str) -> dict:
    """基于关键词对菜品进行分类和风险标注"""
    protein_kw = ["鸡", "鱼", "虾", "牛", "猪", "羊", "蛋", "豆腐", "豆", "肉", "排", "腱", "腿"]
    veggie_kw  = ["菜", "瓜", "笋", "菇", "蘑", "芹", "菠", "白菜", "花椰", "西兰", "生菜", "黄瓜", "番茄", "茄子", "豆角"]
    carb_kw    = ["饭", "面", "粉", "饼", "包", "馒", "粥", "米", "馍", "糕", "饺", "馄饨", "锅贴"]
    fried_kw   = ["炸", "煎", "红烧", "干锅", "爆炒", "油淋", "酥", "锅包"]
    light_kw   = ["蒸", "煮", "白灼", "清炒", "凉拌", "水煮", "炖", "清蒸"]
    spicy_kw   = ["辣", "麻", "椒", "火锅", "川", "湘", "剁椒"]

    category = "其他"
    cooking_method = "未知"
    risk_tags = []

    for kw in protein_kw:
        if kw in name:
            category = "蛋白质"; break
    for kw in veggie_kw:
        if kw in name:
            category = "蔬菜"; break
    for kw in carb_kw:
        if kw in name:
            category = "主食"; break
    for kw in fried_kw:
        if kw in name:
            cooking_method = "高油"; risk_tags.append("高油"); break
    for kw in light_kw:
        if kw in name:
            cooking_method = "清淡"; break
    for kw in spicy_kw:
        if kw in name:
            risk_tags.append("辛辣"); break
    if any(k in name for k in ["糖", "甜", "蜜"]):
        risk_tags.append("高糖")

    return {"category": category, "cooking_method": cooking_method, "risk_tags": risk_tags}

def generate_mock_menu():
    return [
        "白灼虾", "清蒸鲈鱼", "水煮牛肉", "红烧肉", "宫保鸡丁",
        "麻婆豆腐", "炒青菜", "凉拌黄瓜", "番茄炒蛋", "蒜蓉西兰花",
        "米饭", "炒面", "紫菜蛋花汤", "冬瓜排骨汤", "酸辣土豆丝",
        "干煸四季豆", "清炒时蔬", "糖醋里脊", "口水鸡", "蒸蛋羹"
    ]

def build_recommendation(dishes: list, profile: dict, mood: str) -> dict:
    """规则引擎：根据用户目标和心情偏好生成推荐"""
    goal = profile.get("goal", "维持")
    diet_prefs = profile.get("diet_prefs", [])
    
    # 过滤
    filtered = []
    for dish in dishes:
        skip = False
        for pref in diet_prefs:
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

    # 打分
    scored = []
    for dish in filtered:
        info = classify_dish(dish)
        score = 0
        if goal == "增肌":
            if info["category"] == "蛋白质": score += 10
            if info["cooking_method"] == "清淡": score += 3
            if "高油" in info["risk_tags"]: score -= 3
        elif goal == "减脂":
            if info["category"] == "蔬菜": score += 8
            if info["category"] == "蛋白质" and info["cooking_method"] == "清淡": score += 7
            if "高油" in info["risk_tags"]: score -= 5
            if "高糖" in info["risk_tags"]: score -= 5
            if info["category"] == "主食": score -= 2
        else:
            if info["category"] in ["蛋白质", "蔬菜"]: score += 5
            if info["cooking_method"] == "清淡": score += 2

        if mood == "更饱":
            if info["category"] in ["蛋白质", "主食"]: score += 4
        elif mood == "更便宜":
            if info["category"] == "蔬菜": score += 3
            if info["category"] == "主食": score += 2
        elif mood == "更清淡":
            if info["cooking_method"] == "清淡": score += 5
            if "高油" in info["risk_tags"]: score -= 5
        elif mood == "更好吃":
            if any(k in dish for k in ["红烧", "宫保", "糖醋", "口水", "干锅"]): score += 4

        scored.append((dish, score, info))

    scored.sort(key=lambda x: x[1], reverse=True)

    # 多样性选择
    selected = []
    has_protein = has_veggie = False
    for dish, score, info in scored:
        if len(selected) >= 3: break
        if info["category"] == "蛋白质" and not has_protein:
            selected.append((dish, score, info)); has_protein = True
        elif info["category"] == "蔬菜" and not has_veggie:
            selected.append((dish, score, info)); has_veggie = True
        elif info["category"] not in ["蛋白质", "蔬菜"]:
            selected.append((dish, score, info))
    for dish, score, info in scored:
        if len(selected) >= 3: break
        if (dish, score, info) not in selected:
            selected.append((dish, score, info))

    # 推荐理由
    recommendations = []
    for dish, score, info in selected:
        reasons = []
        if info["category"] == "蛋白质": reasons.append("优质蛋白来源")
        if info["category"] == "蔬菜": reasons.append("富含膳食纤维")
        if info["cooking_method"] == "清淡": reasons.append("烹饪方式清淡")
        if "高油" in info["risk_tags"]: reasons.append("注意：油脂较高")
        if not reasons: reasons.append("营养均衡")
        recommendations.append({
            "name": dish,
            "reason": "、".join(reasons),
            "category": info["category"]
        })

    # 下单备注
    notes = []
    has_fried = any("高油" in info["risk_tags"] for _, _, info in selected)
    if goal == "减脂":
        notes.extend(["酱料/汤汁分开放", "主食减半或换杂粮", "少油少盐"])
        if has_fried: notes.append("能换成蒸/煮就不要炸")
    elif goal == "增肌":
        notes.extend(["多加青菜/加一份青菜", "不加糖"])
        if has_fried: notes.append("少油，能蒸煮优先")
    else:
        notes.extend(["少油少盐", "酱料分开放"])
    if mood == "更清淡":
        notes.insert(0, "清淡为主，少油少盐")

    alternatives = [d for d, _, _ in scored[3:6]]

    return {
        "recommendations": recommendations,
        "order_notes": notes,
        "alternatives": alternatives,
        "mood": mood,
        "goal": goal
    }

# ── CORS Headers ──────────────────────────────────────────
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Content-Type": "application/json"
}

# ── Vercel Handler ────────────────────────────────────────
class handler(BaseHTTPRequestHandler):

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        params = {}
        if "?" in self.path:
            qs = self.path.split("?", 1)[1]
            for part in qs.split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = v

        if path == "/api/healthz":
            self._send_json(200, {
                "status": "ok",
                "mock_mode": MOCK_MODE,
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            })

        elif path.startswith("/api/profile/"):
            user_id = path.split("/")[-1]
            if user_id in _profiles:
                self._send_json(200, _profiles[user_id])
            else:
                self._send_json(404, {"error": "用户资料不存在"})

        elif path == "/api/history":
            user_id = params.get("user_id")
            if user_id:
                records = [r for r in _history if r.get("user_id") == user_id]
            else:
                records = _history[-20:]
            self._send_json(200, {"history": records, "total": len(records)})

        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        content_type = self.headers.get("Content-Type", "")
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if path == "/api/profile":
            try:
                data = json.loads(body.decode("utf-8"))
                user_id = str(uuid.uuid4())[:8]
                _profiles[user_id] = data
                tdee = calculate_bmr(data)
                self._send_json(200, {
                    "user_id": user_id,
                    "tdee": round(tdee),
                    "message": "用户资料保存成功"
                })
            except Exception as e:
                self._send_json(400, {"error": str(e)})

        elif path == "/api/analyze-menu":
            try:
                # 解析 multipart/form-data
                user_id = None
                mood = "均衡"

                if "multipart/form-data" in content_type:
                    boundary = content_type.split("boundary=")[-1].encode()
                    # 简单解析 multipart
                    parts = body.split(b"--" + boundary)
                    for part in parts:
                        if b"Content-Disposition" not in part:
                            continue
                        header_end = part.find(b"\r\n\r\n")
                        if header_end == -1:
                            continue
                        headers_raw = part[:header_end].decode("utf-8", errors="ignore")
                        value = part[header_end + 4:].rstrip(b"\r\n--")
                        if 'name="user_id"' in headers_raw:
                            user_id = value.decode("utf-8", errors="ignore").strip()
                        elif 'name="mood"' in headers_raw:
                            mood = value.decode("utf-8", errors="ignore").strip()
                elif "application/json" in content_type:
                    data = json.loads(body.decode("utf-8"))
                    user_id = data.get("user_id")
                    mood = data.get("mood", "均衡")

                if not user_id or user_id not in _profiles:
                    # 使用默认 demo 资料
                    demo_profile = {
                        "gender": "male", "age": 28, "height": 170,
                        "weight": 65, "goal": "减脂",
                        "diet_prefs": [], "activity_level": "中", "allergies": []
                    }
                    profile = demo_profile
                else:
                    profile = _profiles[user_id]

                dishes = generate_mock_menu()
                result = build_recommendation(dishes, profile, mood)

                record = {
                    "id": str(uuid.uuid4())[:8],
                    "user_id": user_id or "demo",
                    "timestamp": datetime.now().isoformat(),
                    "dishes_count": len(dishes),
                    "mood": mood,
                    "ocr_source": "mock",
                    **result
                }
                _history.append(record)

                self._send_json(200, {
                    "dishes": dishes,
                    "ocr_source": "mock",
                    **result,
                    "disclaimer": "⚠️ 本推荐仅供参考，非医疗建议。慢性病患者请咨询医生或营养师。"
                })
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        else:
            self._send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        pass  # 禁用默认日志输出
