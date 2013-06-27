import json

from taal import TranslationContextManager, translation_manager


class TypeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso types """

    context = "taal:kaiso_type"

    def __init__(self, manager, **kwargs):
        self.manager = manager

    def list_message_ids(self):
        manager = self.manager
        type_hierarchy = manager.get_type_hierarchy()
        return (type_[0] for type_ in type_hierarchy)

translation_manager.register(TypeTranslationContextManager)


class AttributeTranslationContextManager(TranslationContextManager):
    """ TranslationContextManager for Kaiso attributes """

    context = "taal:kaiso_attr"

    def __init__(self, manager, **kwargs):
        self.manager = manager

    @staticmethod
    def get_message_id(type_id, attr):
        return json.dumps(
            [type_id, attr.name]
        )

    def list_message_ids(self):
        manager = self.manager
        type_hierarchy = manager.get_type_hierarchy()
        for type_id, bases, attrs in type_hierarchy:
            for attr in attrs:
                yield self.get_message_id(
                    type_id, attr)

translation_manager.register(AttributeTranslationContextManager)
