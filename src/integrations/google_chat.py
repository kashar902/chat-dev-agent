import re


def parse_google_chat_message(event: dict) -> dict:
    message = event.get("message", {})
    text = message.get("text", "")
    space = message.get("space", {}).get("name", "")
    thread = message.get("thread", {}).get("name", "")
    sender = message.get("sender", {}).get("name", "")

    text = re.sub(r"<[^>]+>", "", text).strip()

    return {
        "text": text,
        "space_id": space,
        "thread_id": thread or space,
        "sender_id": sender,
        "message_id": message.get("name", ""),
    }


def build_text_response(text: str) -> dict:
    return {"text": text}


def build_card_response(title: str, sections: list[dict]) -> dict:
    widgets = []
    for section in sections:
        if "text" in section:
            widgets.append({
                "decoratedText": {
                    "topLabel": section.get("label", ""),
                    "text": section["text"],
                }
            })
        elif "button" in section:
            widgets.append({
                "buttonList": {
                    "buttons": [
                        {
                            "text": section["button"]["text"],
                            "onClick": {
                                "openLink": {"url": section["button"]["url"]}
                            },
                        }
                    ]
                }
            })

    return {
        "cardsV2": [
            {
                "cardId": "agent-response",
                "card": {
                    "header": {"title": title},
                    "sections": [{"widgets": widgets}],
                },
            }
        ]
    }
