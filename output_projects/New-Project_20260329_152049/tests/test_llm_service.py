import pytest
from unittest.mock import patch, MagicMock
from services.llm_service import extract_fields, generate_reply


@patch("services.llm_service.openai.ChatCompletion.create")
def test_extract_fields(mock_create):
    # 模擬 OpenAI 回傳
    mock_create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"customer_name":"王大明","product_id":"P12345","summary":"無法開機","suggested_close_date":"2024-07-01"}'
                )
            )
        ]
    )

    raw_text = "客戶王大明反應產品 P12345 無法開機，希望盡快處理。"
    result = extract_fields(raw_text)

    assert result["customer_name"] == "王大明"
    assert result["product_id"] == "P12345"
    assert result["summary"] == "無法開機"
    assert result["suggested_close_date"] == "2024-07-01"


@patch("services.llm_service.openai.ChatCompletion.create")
def test_generate_reply(mock_create):
    mock_create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="親愛的客戶，感謝您的來信..."))]
    )

    ticket_info = {
        "customer_name": "王大明",
        "product_id": "P12345",
        "summary": "無法開機",
    }
    reply = generate_reply(ticket_info)

    assert "親愛的客戶" in reply
    assert "王大明" in reply