"""核心模块 - DeepSeek LLM 客户端（支持流式）"""
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

class DeepSeekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = "https://api.deepseek.com/v1"

    def chat(self, messages, stream=False, temperature=0.5, max_tokens=2048):
        """发送聊天请求，返回完整响应或流式迭代器"""
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            },
            timeout=120,
            stream=stream
        )

        if resp.status_code != 200:
            raise Exception(f"API错误 ({resp.status_code}): {resp.text[:200]}")

        if stream:
            return self._stream_response(resp)
        else:
            return resp.json()["choices"][0]["message"]["content"]

    def _stream_response(self, resp):
        """SSE 流式解析器"""
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    def ask(self, system_prompt, user_message, stream=False):
        """快捷方法：单轮对话"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages, stream=stream)

# 全局单例
llm = DeepSeekClient()
