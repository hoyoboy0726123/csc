import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.llm_orchestrator import LLMOrchestrator
from backend.services.model_router import ModelRouter
from backend.services.prompt_chains import PromptChains
from backend.utils.exceptions import LLMError, ModelRouterError


@pytest.fixture
def mock_model_router():
    router = MagicMock(spec=ModelRouter)
    router.call_gemini = AsyncMock(return_value="gemini response")
    router.call_groq = AsyncMock(return_value="groq response")
    router.select_model = MagicMock(return_value=("gemini", "gemini-1.5-pro"))
    return router


@pytest.fixture
def mock_prompt_chains():
    chains = MagicMock(spec=PromptChains)
    chains.build_prd_chain.return_value = "PRD prompt chain"
    chains.build_code_chain.return_value = "Code prompt chain"
    chains.build_fix_chain.return_value = "Fix prompt chain"
    return chains


@pytest.fixture
def orchestrator(mock_model_router, mock_prompt_chains):
    with patch("backend.services.llm_orchestrator.ModelRouter", return_value=mock_model_router), \
         patch("backend.services.llm_orchestrator.PromptChains", return_value=mock_prompt_chains):
        orch = LLMOrchestrator()
        orch.router = mock_model_router
        orch.chains = mock_prompt_chains
        return orch


@pytest.mark.asyncio
async def test_generate_prd_success(orchestrator, mock_model_router):
    user_input = "我想做一個線上書店"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "# 線上書店 PRD\n## 功能列表\n1. 用戶註冊登入\n2. 瀏覽書籍\n3. 購物車\n4. 訂單管理"

    result = await orchestrator.generate_prd(user_input, model_key)

    assert "線上書店" in result
    assert "功能列表" in result
    mock_model_router.call_gemini.assert_awaited_once()
    orchestrator.chains.build_prd_chain.assert_called_once_with(user_input)


@pytest.mark.asyncio
async def test_generate_prd_llm_error(orchestrator, mock_model_router):
    user_input = "我想做一個線上書店"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.side_effect = Exception("LLM call failed")

    with pytest.raises(LLMError, match="LLM call failed"):
        await orchestrator.generate_prd(user_input, model_key)


@pytest.mark.asyncio
async def test_generate_code_success(orchestrator, mock_model_router):
    prd_md = "# 線上書店 PRD\n## 功能列表\n1. 用戶註冊登入"
    stack = "python"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "```python\n# main.py\nprint('Hello Bookstore')\n```"

    result = await orchestrator.generate_code(prd_md, stack, model_key)

    assert "main.py" in result
    assert "Hello Bookstore" in result
    mock_model_router.call_gemini.assert_awaited_once()
    orchestrator.chains.build_code_chain.assert_called_once_with(prd_md, stack)


@pytest.mark.asyncio
async def test_generate_code_model_router_error(orchestrator, mock_model_router):
    prd_md = "# 線上書店 PRD"
    stack = "python"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.side_effect = ModelRouterError("Model not available")

    with pytest.raises(ModelRouterError, match="Model not available"):
        await orchestrator.generate_code(prd_md, stack, model_key)


@pytest.mark.asyncio
async def test_fix_code_success(orchestrator, mock_model_router):
    error_msg = "ModuleNotFoundError: No module named 'flask'"
    code_snippet = "import flask"
    stack = "python"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = "```python\nimport flask\n# fixed\n```"

    result = await orchestrator.fix_code(error_msg, code_snippet, stack, model_key)

    assert "import flask" in result
    mock_model_router.call_groq.assert_awaited_once()
    orchestrator.chains.build_fix_chain.assert_called_once_with(error_msg, code_snippet, stack)


@pytest.mark.asyncio
async def test_fix_code_empty_response(orchestrator, mock_model_router):
    error_msg = "SyntaxError"
    code_snippet = "print('hello'"
    stack = "python"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = ""

    with pytest.raises(LLMError, match="No fix generated"):
        await orchestrator.fix_code(error_msg, code_snippet, stack, model_key)


@pytest.mark.asyncio
async def test_generate_prd_with_groq(orchestrator, mock_model_router):
    user_input = "Build a todo app"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = "# Todo App PRD"

    result = await orchestrator.generate_prd(user_input, model_key)

    assert "Todo App" in result
    mock_model_router.call_groq.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_code_with_react_stack(orchestrator, mock_model_router):
    prd_md = "# Todo App"
    stack = "react"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "```jsx\nfunction App() { return <div>Todo</div>; }\n```"

    result = await orchestrator.generate_code(prd_md, stack, model_key)

    assert "function App" in result
    orchestrator.chains.build_code_chain.assert_called_once_with(prd_md, stack)


@pytest.mark.asyncio
async def test_fix_code_with_nodejs_stack(orchestrator, mock_model_router):
    error_msg = "Cannot find module 'express'"
    code_snippet = "const express = require('express');"
    stack = "nodejs"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = "```javascript\nconst express = require('express');\n// fixed\n```"

    result = await orchestrator.fix_code(error_msg, code_snippet, stack, model_key)

    assert "require('express')" in result
    orchestrator.chains.build_fix_chain.assert_called_once_with(error_msg, code_snippet, stack)


@pytest.mark.asyncio
async def test_generate_prd_with_multiline_input(orchestrator, mock_model_router):
    user_input = """我們要做一個線上課程平台，
支援老師開課、學生購買、金流串接，
還要有後台管理與報表功能。"""
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "# 線上課程平台 PRD"

    result = await orchestrator.generate_prd(user_input, model_key)

    assert "線上課程平台" in result
    mock_model_router.call_gemini.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_code_with_empty_prd(orchestrator, mock_model_router):
    prd_md = ""
    stack = "python"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "# Empty PRD response"

    result = await orchestrator.generate_code(prd_md, stack, model_key)

    assert "Empty PRD response" in result
    orchestrator.chains.build_code_chain.assert_called_once_with("", stack)


@pytest.mark.asyncio
async def test_fix_code_with_long_error_traceback(orchestrator, mock_model_router):
    error_msg = """Traceback (most recent call last):
  File "main.py", line 10, in <module>
    raise ValueError("Invalid config")
ValueError: Invalid config"""
    code_snippet = "raise ValueError('Invalid config')"
    stack = "python"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = "```python\n# fixed code\n```"

    result = await orchestrator.fix_code(error_msg, code_snippet, stack, model_key)

    assert "fixed code" in result
    mock_model_router.call_groq.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_prd_with_unicode_content(orchestrator, mock_model_router):
    user_input = "做一個支援中文、English、🚀 的應用"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "# Unicode PRD"

    result = await orchestrator.generate_prd(user_input, model_key)

    assert "Unicode PRD" in result
    mock_model_router.call_gemini.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_code_with_special_stack_name(orchestrator, mock_model_router):
    prd_md = "# Special stack test"
    stack = "nextjs"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "```jsx\nexport default function Home() {}\n```"

    result = await orchestrator.generate_code(prd_md, stack, model_key)

    assert "export default function Home" in result
    orchestrator.chains.build_code_chain.assert_called_once_with(prd_md, stack)


@pytest.mark.asyncio
async def test_fix_code_with_no_error_message(orchestrator, mock_model_router):
    error_msg = ""
    code_snippet = "print('hello')"
    stack = "python"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = "```python\nprint('hello world')\n```"

    result = await orchestrator.fix_code(error_msg, code_snippet, stack, model_key)

    assert "hello world" in result
    orchestrator.chains.build_fix_chain.assert_called_once_with("", code_snippet, stack)


@pytest.mark.asyncio
async def test_generate_prd_with_max_length_input(orchestrator, mock_model_router):
    user_input = "我想做一個線上書店" * 100
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "# Long input PRD"

    result = await orchestrator.generate_prd(user_input, model_key)

    assert "Long input PRD" in result
    mock_model_router.call_gemini.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_code_with_minimal_prd(orchestrator, mock_model_router):
    prd_md = "# A"
    stack = "python"
    model_key = "gemini-1.5-pro"
    mock_model_router.call_gemini.return_value = "```python\nprint('A')\n```"

    result = await orchestrator.generate_code(prd_md, stack, model_key)

    assert "print('A')" in result
    orchestrator.chains.build_code_chain.assert_called_once_with("# A", stack)


@pytest.mark.asyncio
async def test_fix_code_with_multiple_errors(orchestrator, mock_model_router):
    error_msg = "IndentationError\nNameError"
    code_snippet = "def foo()\nprint(x)"
    stack = "python"
    model_key = "groq-llama3-70b"
    mock_model_router.call_groq.return_value = "```python\ndef foo():\n    print('fixed')\n```"

    result = await orchestrator.fix_code(error_msg, code_snippet, stack, model_key)

    assert "def foo():" in result
    mock_model_router.call_groq.assert_awaited_once()