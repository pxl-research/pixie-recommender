from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class QuestionConfig:
    attribute_name: str
    text: str
    required: bool = True


@dataclass(frozen=True)
class ConversationFlowConfig:
    questions: List[QuestionConfig]


CONVERSATION_FLOWS = {
    "printers": ConversationFlowConfig(
        questions=[
            QuestionConfig("budget", "Wat is je budget voor een printer?"),
            QuestionConfig("brand", "Heb je een voorkeur voor een merk?", required=False),
            QuestionConfig("technology", "Welke printtechnologie zoek je?", required=False),
        ]
    ),
    "laptops": ConversationFlowConfig(
        questions=[
            QuestionConfig("budget", "Wat is je budget voor een laptop?"),
            QuestionConfig("brand", "Heb je een voorkeursmerk?", required=False),
            QuestionConfig("screen_size", "Welke schermgrootte zoek je?", required=False),
        ]
    ),
    "smartphones": ConversationFlowConfig(
        questions=[
            QuestionConfig("budget", "Wat is je budget voor een smartphone?"),
            QuestionConfig("brand", "Welk merk prefereer je?", required=False),
            QuestionConfig("screen_size", "Welke schermgrootte wil je?", required=False),
        ]
    ),
    "computers": ConversationFlowConfig(
        questions=[
            QuestionConfig("budget", "Wat is je budget voor een computer?"),
            QuestionConfig("brand", "Heb je een voorkeursmerk?", required=False),
            QuestionConfig("processor", "Welke processor heeft je voorkeur?", required=False),
        ]
    ),
}
