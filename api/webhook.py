from flask import Flask, request
from twilio.rest import Client
from openai import OpenAI
import os

app = Flask(__name__)

twilio_client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])

deepseek_client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

conversation_history = {}

SYSTEM_PROMPT = """你是 MikeStyle 的售前顾问，负责通过 WhatsApp 回复客户咨询。

【品牌介绍】
MikeStyle 是一个主打简约休闲风格的服装品牌，所有产品均提供S/M/L/XL四个尺码，支持7天无理由退换货。

【产品目录】

▌ 上装系列
- 经典白色棉质T恤｜$25｜100%纯棉，透气舒适，百搭款
- 宽松条纹卫衣｜$58｜加绒保暖，蓝白条纹，秋冬必备
- 亚麻休闲衬衫｜$72｜轻薄透气，米白色，适合商务休闲场合

▌ 下装系列
- 直筒牛仔裤｜$89｜经典蓝色水洗，修身显腿长
- 运动休闲短裤｜$45｜速干面料，黑/灰/藏青三色可选
- 高腰阔腿裤｜$95｜垂感面料，奶茶色，显高显瘦

【优惠政策】
- 首单九折优惠
- 购满$150包邮
- 购买链接：https://mikestyle.com/shop

【回复原则】
- 语气友好简洁，像朋友聊天一样自然
- 客户问款式时主动推荐并说明适合的场合和搭配
- 客户有购买意向时发送购买链接
- 遇到投诉或退款问题回复"我帮您转接专属顾问"
- 不能承诺额外折扣
"""

@app.route("/api/webhook", methods=["POST"])
def webhook():
    try:
        user_msg = request.form.get("Body", "")
        user_phone = request.form.get("From", "")

        history = conversation_history.get(user_phone, [])
        history.append({"role": "user", "content": user_msg})

        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history[-20:],
            max_tokens=500
        )

        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        conversation_history[user_phone] = history

        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=user_phone,
            body=reply
        )

        return "", 200

    except Exception as e:
        twilio_client.messages.create(
            from_="whatsapp:+14155238886",
            to=request.form.get("From", ""),
            body=f"DEBUG: {str(e)}"
        )
        return str(e), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)