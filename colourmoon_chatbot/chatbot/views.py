from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Lead, SupportTicket
import openai
import json, re, traceback

# ✅ OpenAI client
openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

user_sessions = {}

LEAD_KEYWORDS = ["website", "app", "ios", "android"]
SEO_KEYWORDS = ["seo", "search engine", "google rank"]
DM_KEYWORDS = ["digital marketing", "facebook ads", "instagram", "leads"]
SUPPORT_KEYWORDS = ["issue", "not working", "error", "bug", "down", "support", "problem", "fail"]


def chatbot_home(request):
    return render(request, "index.html")


@csrf_exempt
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        if not message:
            return JsonResponse({"reply": "Hey there! 😊 What's on your mind today?"})

        if not request.session.session_key:
            request.session.save()
        session_id = request.session.session_key

        session = user_sessions.get(session_id, {
            "mode": None,
            "data": {},
            "requirement": None,
            "submitted": False,
            "step": 0,
            "ip": get_ip(request),
            "browser": request.META.get("HTTP_USER_AGENT", "Unknown"),
            "referrer": request.META.get("HTTP_REFERER", "Unknown")
        })

        message_lower = message.lower()

        if message_lower in ["hi", "hello", "start", "new"]:
            user_sessions.pop(session_id, None)
            return JsonResponse({"reply": "Hey! 👋 I'm your assistant from The Colour Moon. Need help with a website, app, SEO, or support? 😄"})

        if session.get("submitted"):
            if any(k in message_lower for k in LEAD_KEYWORDS + SEO_KEYWORDS + DM_KEYWORDS + SUPPORT_KEYWORDS):
                user_sessions.pop(session_id, None)
                return JsonResponse({"reply": "Sure! Let's get started with your next query 😊 What service do you need help with now?"})
            return JsonResponse({"reply": "✅ We've saved your details. Our team will contact you shortly. For urgent help, call 📞 8978553778."})

        if not session.get("mode"):
            if any(k in message_lower for k in SUPPORT_KEYWORDS):
                session["mode"] = "support"
                session["requirement"] = message
                user_sessions[session_id] = session
                return JsonResponse({"reply": "Sorry to hear that 😔 Please share your domain and describe the issue you're facing."})
            elif any(k in message_lower for k in SEO_KEYWORDS):
                session["mode"] = "seo"
                session["requirement"] = message
                user_sessions[session_id] = session
                return JsonResponse({"reply": "Great! 📈 Could you share your website URL and what goals you have for SEO? (e.g., improve ranking, traffic)"})
            elif any(k in message_lower for k in DM_KEYWORDS):
                session["mode"] = "dm"
                session["requirement"] = message
                user_sessions[session_id] = session
                return JsonResponse({"reply": "Nice! 📢 Which platform do you want to market on (e.g., Instagram, Facebook)?"})
            elif any(k in message_lower for k in LEAD_KEYWORDS):
                session["mode"] = "lead"
                session["requirement"] = message
                user_sessions[session_id] = session
                return JsonResponse({"reply": "Awesome! 😊 Could you describe your requirement in detail?"})
            else:
                return JsonResponse({"reply": ask_ai(message)})

        data = session["data"]

        if session["mode"] == "support":
            if not data.get("domain"):
                domain = extract_domain(message)
                if domain:
                    data["domain"] = domain
                    user_sessions[session_id] = session
                    return JsonResponse({"reply": "Got it 👍 Now briefly describe the issue you're facing."})
                return JsonResponse({"reply": "🌐 Please share the domain (e.g., mysite.com)"})

            if not data.get("issue"):
                data["issue"] = message
                user_sessions[session_id] = session
                return JsonResponse({"reply": "👤 Your name please?"})

            if not data.get("name"):
                name = extract_name(message)
                if name:
                    data["name"] = name
                    return JsonResponse({"reply": "📞 Your phone number?"})
                return JsonResponse({"reply": "👤 Please share your name."})

            if not data.get("phone"):
                phone = extract_phone(message)
                if phone:
                    data["phone"] = phone
                    SupportTicket.objects.create(
                        name=data["name"],
                        phone=data["phone"],
                        domain=data["domain"],
                        issue=data["issue"],
                        ip=session["ip"],
                        browser=session["browser"],
                        referrer=session["referrer"],
                        created_at=timezone.now()
                    )
                    session["submitted"] = True
                    return JsonResponse({"reply": "✅ Ticket logged! We'll contact you soon. 📞 8978553778"})
                return JsonResponse({"reply": "📞 Enter a valid phone number (e.g., 9876543210)."})

        if session["mode"] in ["lead", "seo", "dm"]:
            steps = {
                "lead": ["details", "type", "budget", "name", "phone", "email"],  # Removed pages, cms from mandatory
                "seo": ["domain", "goals", "budget", "name", "phone", "email"],
                "dm": ["platform", "goals", "budget", "name", "phone", "email"]
            }

            optional_fields = {
                "lead": ["pages", "cms"],
            }

            prompts = {
                "details": "Just to confirm – do you have a reference like BookMyShow or similar?",
                "type": "Is this for booking, e-commerce, or something else?",
                "budget": "💰 What's your estimated budget? (e.g., 30000, 45k)",
                "name": "👤 Your name please?",
                "phone": "📞 Your phone number?",
                "email": "📧 Your email address please.",
                "domain": "🌐 Please share your website URL (e.g., mysite.com)",
                "goals": "🎯 What goals do you want to achieve (e.g., more traffic, brand visibility)?",
                "platform": "📢 Which platform are you targeting (e.g., Facebook, Instagram)?"
            }

            for field in steps[session["mode"]]:
                if not data.get(field):
                    value = extract_value(field, message)
                    if value:
                        data[field] = value
                        user_sessions[session_id] = session
                        continue
                    return JsonResponse({"reply": prompts[field]})

            # Collect optional fields like 'pages' and 'cms' once required data is filled
            if session["mode"] == "lead":
                if not data.get("pages") and not data.get("cms"):
                    data["pages"] = extract_value("pages", message)
                    data["cms"] = extract_value("cms", message)
                    user_sessions[session_id] = session
                    return JsonResponse({
                                            "reply": "If you know the number of pages and if CMS is required, please mention them (e.g., 5 pages, CMS yes). Else, we can proceed."})

            # ✅ Save to Lead model
            Lead.objects.create(
                name=data["name"],
                phone=data["phone"],
                email=data["email"],
                service=session["requirement"],
                type=data.get("type", ""),
                pages=data.get("pages", ""),
                cms=data.get("cms", ""),
                payment=data.get("platform", ""),
                budget=data.get("budget", ""),
                requirement=data.get("details") or data.get("goals", ""),
                ip=session["ip"],
                browser=session["browser"],
                referrer=session["referrer"],
                created_at=timezone.now()
            )
            session["submitted"] = True
            return JsonResponse({
                                    "reply": "✅ All done! We've saved your project info. Our team will connect with you shortly. 📞 8978553778"})

        return JsonResponse({"reply": ask_ai(message)})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"reply": "⚠️ Hmm, the assistant had a hiccup! Try again shortly."})


# ------------------ Utilities ------------------

def ask_ai(msg, context="You're a helpful assistant from The Colour Moon. Always respond in 1-2 lines."):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": msg}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI error:", e)
        return "⚠️ The assistant is thinking too hard! Please retry."

def extract_name(text):
    match = re.search(r"(?:i am|this is|name is)?\s*([A-Za-z\s]{3,})", text, re.IGNORECASE)
    return match.group(1).strip().title() if match else None

def extract_phone(text):
    match = re.search(r"\b(\+91)?\d{10}\b", text)
    return match.group(0) if match else None

def extract_email(text):
    match = re.search(r"[a-zA-Z0-9][a-zA-Z0-9._%+-]{2,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None

def extract_budget(text):
    match = re.search(r"(\d{1,6})\s*(k|rs|rupees|inr)?", text.lower())
    if match:
        budget = match.group(1)
        if match.group(2) in ["k", "rs", "rupees", "inr"]:
            budget = str(int(budget) * 1000)
        return budget
    return None

def extract_domain(text):
    match = re.search(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}", text)
    return match.group(0) if match else None

def extract_value(field, msg):
    if field == "name": return extract_name(msg)
    if field == "phone": return extract_phone(msg)
    if field == "email": return extract_email(msg)
    if field == "budget": return extract_budget(msg)
    if field == "domain": return extract_domain(msg)
    if field == "pages": return msg if "page" in msg.lower() else None
    if field == "cms": return msg if "cms" in msg.lower() or msg.lower() in ["yes", "no"] else None
    return msg.strip()


def get_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
