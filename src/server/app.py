from fastapi import FastAPI, Request
from pydantic import BaseModel
from src.agent.core import Agent
from src.integrations.google_chat import parse_google_chat_message, build_text_response
from src.utils.logger import logger


app = FastAPI(
    title="Google Chat Bitbucket Agent",
    description="AI-powered agent for Bitbucket code analysis, feature implementation, and PR creation via Google Chat",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "Webhooks", "description": "Google Chat webhook endpoints"},
        {"name": "Testing", "description": "Test endpoints for debugging"},
        {"name": "Health", "description": "Health check endpoints"},
    ],
)

agent = Agent()


class ChatMessage(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    reply: str


class ErrorResponse(BaseModel):
    error: str


class HealthResponse(BaseModel):
    status: str


@app.post(
    "/webhook/google-chat",
    tags=["Webhooks"],
    summary="Google Chat webhook handler",
    description="Receives messages from Google Chat and routes them to the agent for processing.",
    response_model=None,
)
async def handle_google_chat(request: Request):
    body = await request.json()

    event_type = body.get("type")
    if event_type == "ADDED_TO_SPACE":
        return build_text_response("Hello! I'm your Bitbucket assistant. Ask me to analyze repos, implement features, or create PRs.")

    if event_type == "MESSAGE_RECEIVED":
        parsed = parse_google_chat_message(body)
        text = parsed["text"]
        thread_id = parsed["thread_id"]

        if not text:
            return build_text_response("Please send a message.")

        logger.info(f"Message from {parsed['sender_id']}: {text}")

        try:
            reply = agent.process(text, thread_id)
            return build_text_response(reply)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return build_text_response(f"Error: {str(e)}")

    return build_text_response("Event not handled.")


@app.post(
    "/webhook/test",
    tags=["Testing"],
    summary="Test the agent",
    description="Send a test message to the agent without Google Chat. Useful for debugging and development.",
    response_model=ChatMessageResponse,
    responses={
        200: {"description": "Agent response"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    },
)
async def test_webhook(body: ChatMessage):
    try:
        reply = agent.process(body.message, "test")
        return ChatMessageResponse(reply=reply)
    except Exception as e:
        return ErrorResponse(error=str(e))


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Check if the agent service is running.",
    response_model=HealthResponse,
)
async def health():
    return HealthResponse(status="ok")
