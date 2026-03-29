import streamlit as st
import msal
from datetime import datetime
from typing import Optional
from .config import get_settings
from .models.user import User

settings = get_settings()

def _build_msal_app():
    return msal.ConfidentialClientApplication(
        settings.AZURE_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}",
        client_credential=settings.AZURE_CLIENT_SECRET,
    )

def _get_token_from_cache():
    if "token_cache" in st.session_state and st.session_state.token_cache:
        cache = msal.SerializableTokenCache()
        cache.deserialize(st.session_state.token_cache)
        cca = _build_msal_app()
        cca.token_cache = cache
        accounts = cca.get_accounts()
        if accounts:
            result = cca.acquire_token_silent(
                scopes=["User.Read"], account=accounts[0]
            )
            if "access_token" in result:
                st.session_state.token_cache = cache.serialize()
                return result
    return None

def login() -> Optional[User]:
    token_result = _get_token_from_cache()
    if token_result and "access_token" in token_result:
        import requests
        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token_result['access_token']}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            user = User(
                id=data["id"],
                name=data["displayName"],
                email=data["mail"] or data["userPrincipalName"],
                role="agent",
            )
            st.session_state.user = user
            return user
        else:
            st.session_state.pop("token_cache", None)

    cca = _build_msal_app()
    flow = cca.initiate_auth_code_flow(
        scopes=["User.Read"], redirect_uri=settings.AZURE_REDIRECT_URI
    )
    st.session_state.auth_flow = flow
    auth_url = flow["auth_uri"]
    st.markdown(
        f'<a href="{auth_url}" target="_self">'
        f'<button style="background-color:#0078d4;color:white;border:none;padding:8px 16px;border-radius:4px;">登入</button></a>',
        unsafe_allow_html=True,
    )
    return None

def logout() -> None:
    st.session_state.pop("user", None)
    st.session_state.pop("token_cache", None)
    st.markdown(
        f'<a href="https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/logout" target="_self">'
        f'<button style="background-color:#d13438;color:white;border:none;padding:8px 16px;border-radius:4px;">登出</button></a>',
        unsafe_allow_html=True,
    )

def get_current_user() -> Optional[User]:
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    token_result = _get_token_from_cache()
    if token_result and "access_token" in token_result:
        import requests
        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {token_result['access_token']}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            user = User(
                id=data["id"],
                name=data["displayName"],
                email=data["mail"] or data["userPrincipalName"],
                role="agent",
            )
            st.session_state.user = user
            return user
    return None