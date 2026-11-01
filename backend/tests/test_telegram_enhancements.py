import pytest
from app.services.telegram_service import telegram_service

def test_telegram_clear_and_tracking():
    # Test message tracking and clear functionality
    chat_id = "test_chat_999"
    telegram_service.tracked_messages[chat_id] = [101, 102, 103, 104]
    
    # Process clear update
    update = {
        "message": {
            "message_id": 105,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": 12345, "first_name": "Mustkeem", "username": "mustkeem"},
            "text": "/clear"
        }
    }
    telegram_service.handle_incoming_update(update)
    
    # Tracked messages should be reset after /clear
    assert len(telegram_service.tracked_messages.get(chat_id, [])) == 0

def test_telegram_id_command():
    from_user = {
        "id": 987654321,
        "first_name": "Mustkeem",
        "last_name": "Ahmad",
        "username": "mustkeem_dev",
        "language_code": "en"
    }
    chat_obj = {"id": "987654321", "type": "private"}
    res = telegram_service.build_id_response(from_user, "987654321", 55, chat_obj)
    
    assert "987654321" in res["text"]
    assert "Mustkeem Ahmad" in res["text"]
    assert "@mustkeem_dev" in res["text"]
    assert "TELEGRAM IDENTITY" in res["text"]
    assert "reply_markup" in res
    assert any(btn["text"] == "🧹 Clear Chat" for row in res["reply_markup"]["inline_keyboard"] for btn in row)

def test_telegram_think_command():
    # Test master think response
    res_master = telegram_service.build_think_response()
    assert "AI DEEP THINKING &amp; STRATEGIC CAREER ARCHITECTURE" in res_master["text"]
    assert "Mustkeem Ahmad" in res_master["text"]
    assert "UPES Dehradun MBA" in res_master["text"]
    assert "Jamia Millia Islamia B.Tech" in res_master["text"]
    assert "RLHF" in res_master["text"]
    assert "$40 – $120 / hr" in res_master["text"]

    # Test targeted think response for specific role query
    res_targeted = telegram_service.build_think_response("AI Training Specialist")
    assert "TARGET SPECIFICATION ANALYSIS" in res_targeted["text"]
    assert "Ai Training Specialist" in res_targeted["text"]
    assert "High Alignment" in res_targeted["text"]
    assert "Model Evaluation" in res_targeted["text"]

def test_telegram_interactive_help_system():
    # Test master menu
    res_menu = telegram_service.build_help_master_menu()
    assert "INTERACTIVE HELP CENTER" in res_menu["text"]
    assert "reply_markup" in res_menu
    buttons = [btn["callback_data"] for row in res_menu["reply_markup"]["inline_keyboard"] for btn in row]
    assert "help:search" in buttons
    assert "help:apply" in buttons
    assert "help:naukri" in buttons
    assert "help:think" in buttons
    assert "cmd:clear" in buttons
    assert "cmd:id" in buttons

    # Test category documentation
    res_search = telegram_service.build_help_category("search")
    assert "GLOBAL VACANCY SEARCH" in res_search["text"]
    assert "/search" in res_search["text"]

    res_apply = telegram_service.build_help_category("apply")
    assert "1-CLICK AUTO APPLY" in res_apply["text"]
    assert "/autoapply" in res_apply["text"]

    res_naukri = telegram_service.build_help_category("naukri")
    assert "NAUKRI.COM INDIA" in res_naukri["text"]
    assert "/naukri" in res_naukri["text"]
    assert "Method A URL Ingestion" in res_naukri["text"]

    res_utils = telegram_service.build_help_category("utils")
    assert "/clear" in res_utils["text"]
    assert "/id" in res_utils["text"]

def test_telegram_additional_utility_responses():
    # /tips
    tips = telegram_service.build_tips_response()
    assert "TOP 10 HIGH-CONVERSION APPLICATION STRATEGIES" in tips["text"]
    assert "RLHF" in tips["text"]

    # /faq
    faq = telegram_service.build_faq_response()
    assert "FREQUENTLY ASKED QUESTIONS" in faq["text"]
    assert "Naukri Neo" in faq["text"]

    # /ping
    ping = telegram_service.build_ping_response()
    assert "SYSTEM PING" in ping["text"]
    assert "FastAPI Backend" in ping["text"]

    # /skills
    skills = telegram_service.build_skills_response()
    assert "VERIFIED CANDIDATE SKILL MATRIX" in skills["text"]
    assert "UPES Dehradun" in skills["text"]

    # /roadmap
    roadmap = telegram_service.build_roadmap_response()
    assert "DAILY JOB HUNTER ACTION ROADMAP" in roadmap["text"]
    assert "09:00 AM" in roadmap["text"]

def test_telegram_callback_queries_execution():
    chat_id = "test_cb_123"
    # Test help callback query
    cb_help = {
        "id": "cb_001",
        "data": "help:naukri",
        "from": {"id": 111, "first_name": "Mustkeem"},
        "message": {"message_id": 99, "chat": {"id": chat_id}}
    }
    telegram_service.handle_callback_query(cb_help)

    # Test cmd:think callback query
    cb_think = {
        "id": "cb_002",
        "data": "cmd:think",
        "from": {"id": 111, "first_name": "Mustkeem"},
        "message": {"message_id": 100, "chat": {"id": chat_id}}
    }
    telegram_service.handle_callback_query(cb_think)

    # Test cmd:clear callback query
    cb_clear = {
        "id": "cb_003",
        "data": "cmd:clear",
        "from": {"id": 111, "first_name": "Mustkeem"},
        "message": {"message_id": 101, "chat": {"id": chat_id}}
    }
    telegram_service.handle_callback_query(cb_clear)
    assert len(telegram_service.tracked_messages.get(chat_id, [])) == 0
