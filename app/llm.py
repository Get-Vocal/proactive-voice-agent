import json
import logging
from typing import List

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from app.constants import DEBUG, GREETINGS, LLM_KWARGS, MISTRAL_API_KEY, MODEL, REMINDER_PROMPT, SYSTEM_PROMPT
from app.functions import NAME_TO_FILLER, NAME_TO_FUNCTIONS, TOOLS
from app.schema import CustomLlmRequest, CustomLlmResponse, Utterance


class LlmClient:
    def __init__(self):
        self.client = MistralClient(api_key=MISTRAL_API_KEY)

    def greetings(self):
        response = CustomLlmResponse(
            response_id=0,
            content=GREETINGS,
            content_complete=True,
            end_call=False,
        )
        return response

    def convert_transcript_to_messages(self, transcript: List[Utterance]):
        messages = []
        for utterance in transcript:
            if utterance["role"] == "agent":
                messages.append(ChatMessage(role="assistant", content=utterance["content"]))
            else:
                messages.append(ChatMessage(role="user", content=utterance["content"]))
        return messages

    def prepare_prompt(self, request: CustomLlmRequest):
        transcript_messages = self.convert_transcript_to_messages(request.transcript)
        prompt = [ChatMessage(role="system", content=SYSTEM_PROMPT)] + transcript_messages

        if request.interaction_type == "reminder_required":
            prompt.append(ChatMessage(role="user", content=REMINDER_PROMPT))
        return prompt

    def stream_response(self, request, stream=None):
        logger = logging.getLogger("uvicorn")
        if stream is None:
            prompt = self.prepare_prompt(request)
            stream = self.client.chat_stream(
                model=MODEL, messages=prompt, tools=TOOLS, tool_choice="auto", **LLM_KWARGS
            )
        logged_begin = False
        all_tool_calls = []
        full_content = ""
        for chunk in stream:
            if DEBUG:
                if not logged_begin:
                    logger.info("LLM Response received")
                    logged_begin = True
            # Step 3: Extract the functions
            if len(chunk.choices) == 0:
                continue
            if chunk.choices[0].delta.tool_calls:
                all_tool_calls += chunk.choices[0].delta.tool_calls

            # Parse transcripts
            if chunk.choices[0].delta.content:
                full_content += chunk.choices[0].delta.content
                response = CustomLlmResponse(
                    response_id=request.response_id,
                    content=chunk.choices[0].delta.content,
                    content_complete=False,
                    end_call=False,
                )
                yield response

        # Step 4: Call the functions
        if all_tool_calls:
            tool_results = [ChatMessage(role="assistant", content="", name=None, tool_calls=all_tool_calls)]
            for tool_call in all_tool_calls:
                function_name = tool_call.function.name
                func_resp = NAME_TO_FILLER.get("function_name", "")
                response = CustomLlmResponse(
                    response_id=request.response_id,
                    content=func_resp,
                    content_complete=False,
                    end_call=False,
                )
                yield response

                function_params = json.loads(tool_call.function.arguments)
                function_result = NAME_TO_FUNCTIONS[function_name](**function_params)
                tool_results.append(
                    {
                        "role": "tool",
                        "content": function_result,
                        "name": function_name,
                    }
                )

            stream = self.client.chat_stream(
                model=MODEL, messages=prompt + tool_results, tools=TOOLS, tool_choice="auto", **LLM_KWARGS
            )
            yield from self.stream_response(request, stream)

        else:
            # No functions, complete response
            response = CustomLlmResponse(
                response_id=request.response_id,
                content="",
                content_complete=True,
                end_call=False,
            )
            yield response
