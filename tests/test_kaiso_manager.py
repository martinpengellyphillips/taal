import pytest

from taal import TranslatableString, Translator
from taal.constants import PLACEHOLDER
from taal.exceptions import NoTranslatorRegistered
from taal.kaiso.context_managers import TypeTranslationContextManager
from taal.kaiso.manager import collect_translatables
from taal.kaiso.types import get_context, get_message_id

from tests.models import Translation, CustomFieldsEntity


def test_labeled_hierarchy(session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    entity = next(hierarchy)

    assert isinstance(entity[1], TranslatableString)


def test_labeled_hierarchy_attributes(session, translating_type_heirarchy,
                                      bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    data = {}
    for type_id, label, _, attrs in hierarchy:
        data[type_id] = {
            'label': label,
            'attrs': attrs,
        }

    animal = data['Animal']
    attrs = {attr.name: attr for attr in animal['attrs']}
    name_attr = attrs['name']
    assert isinstance(name_attr.label, TranslatableString)


def test_translating_class_labels(session, translating_type_heirarchy,
                                  bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translatable = TranslatableString(
        context=TypeTranslationContextManager.context,
        message_id='Entity', pending_value='English Entity')

    translator.save_translation(translatable)
    translator.bind(manager)

    hierarchy = manager.get_labeled_type_hierarchy()
    entity = next(hierarchy)

    translated = translator.translate(entity[1])
    assert translated == 'English Entity'


def test_collect_translatables(bound_manager):
    manager = bound_manager

    obj = CustomFieldsEntity(id=1, name="value", extra="", null=None)
    manager.save(obj)

    translatables = collect_translatables(manager, obj)

    for attr_name, expected_value in (
            ("extra", ""), ("name", PLACEHOLDER), ("null", None)):
        translatable = next(translatables)
        assert translatable.context == get_context(manager, obj, attr_name)
        assert translatable.message_id == get_message_id(manager, obj)
        assert translatable.pending_value == expected_value

    with pytest.raises(StopIteration):
        translatables.next()


def test_serialize(session, translating_type_heirarchy, bound_manager):
    manager = bound_manager

    translator = Translator(Translation, session, 'en')
    translator.bind(manager)

    obj = CustomFieldsEntity(id=1, name='English name', extra="", null=None)
    manager.save(obj)

    retrieved = manager.get(CustomFieldsEntity, id=1)
    assert retrieved.name == PLACEHOLDER
    assert retrieved.extra == ""
    assert retrieved.null is None

    serialized = manager.serialize(retrieved)
    assert isinstance(serialized['name'], TranslatableString)
    assert serialized['extra'] == ""
    assert serialized['null'] is None

    translated = translator.translate(serialized)
    assert translated['name'] == 'English name'
    assert translated['extra'] == ""
    assert translated['null'] is None


def test_save(session_cls, bound_manager):
    manager = bound_manager

    def check_value(obj, attr_name, expected_value):
        context = get_context(manager, obj, attr_name)
        assert session_cls().query(Translation).filter_by(
            context=context).one().value == expected_value

    obj = CustomFieldsEntity(id=1, name="value", extra="", null=None)
    manager.save(obj)
    assert session_cls().query(Translation).count() == 1
    check_value(obj, "name", "value")

    obj.extra = "non-empty string"
    manager.save(obj)
    assert session_cls().query(Translation).count() == 2
    check_value(obj, "extra", "non-empty string")

    obj.null = "not null"
    manager.save(obj)
    assert session_cls().query(Translation).count() == 3
    check_value(obj, "null", "not null")

    obj.extra = ""
    manager.save(obj)
    assert session_cls().query(Translation).count() == 2

    obj.null = None
    manager.save(obj)
    assert session_cls().query(Translation).count() == 1


def test_delete(session_cls, bound_manager):
    manager = bound_manager

    obj1 = CustomFieldsEntity(id=1, name="value", extra="", null=None)
    obj2 = CustomFieldsEntity(id=2, name="value", extra="", null=None)
    manager.save(obj1)
    manager.save(obj2)
    assert session_cls().query(Translation).count() == 2

    manager.delete(obj1)
    assert session_cls().query(Translation).count() == 1

    manager.delete(obj2)
    assert session_cls().query(Translation).count() == 0


def test_missing_bind(session, translating_manager):
    manager = translating_manager
    obj = CustomFieldsEntity(id=1, name='English name')
    with pytest.raises(NoTranslatorRegistered):
        manager.save(obj)
