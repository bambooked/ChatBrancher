from domain.entities.message_entity import MessageEntity

def trasnport_message_entity(
        message_entity_list:list[MessageEntity]
        ) -> list[dict]:
    ""
    return [
        {
            "role": message_entity.role.value,
            "content": message_entity.content
        }
        for message_entity in message_entity_list
        ]
