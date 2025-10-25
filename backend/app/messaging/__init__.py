"""Messaging Layer with lazy imports.

Prevents optional dependencies like confluent_kafka/avro from being imported
eagerly in test environments or when not installed.
"""

import importlib
from typing import TYPE_CHECKING

__all__ = [
    "KafkaProducerClient",
    "KafkaConsumerClient",
    "KafkaTopics",
    "create_topics",
]

_LAZY = {
    "KafkaProducerClient": ("app.messaging.kafka_client", "KafkaProducerClient"),
    "KafkaConsumerClient": ("app.messaging.kafka_client", "KafkaConsumerClient"),
    "KafkaTopics": ("app.messaging.kafka_client", "KafkaTopics"),
    "create_topics": ("app.messaging.kafka_client", "create_topics"),
}

def __getattr__(name: str):
    target = _LAZY.get(name)
    if not target:
        raise AttributeError(name)
    module_name, attr = target
    module = importlib.import_module(module_name)
    return getattr(module, attr)

if TYPE_CHECKING:  # pragma: no cover
    from .kafka_client import KafkaProducerClient, KafkaConsumerClient, KafkaTopics, create_topics  # noqa: F401
