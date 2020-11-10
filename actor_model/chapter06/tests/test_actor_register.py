"""
测试register功能.
Notes:
https://learning-pytest.readthedocs.io/zh/latest/doc/fixture/intro.html
"""

import pytest
from ..actor_register import ActorRegistry


@pytest.fixture(scope="module")
def actor_register():
    actor_refs = ['Actor_ref1', 'Actor_ref2', 'Actor_ref3']
    for ref in actor_refs:
        ActorRegistry.register(ref)

    return ActorRegistry


def test_actor_ref_register(actor_register):
    assert actor_register.get_all() == ['Actor_ref1', 'Actor_ref2', 'Actor_ref3']
    assert len(actor_register.get_all()) == 3


def test_actor_ref_unregister_an_actor_ref(actor_register):
    actor_register.unregister('Actor_ref1')
    assert actor_register.get_all() == ['Actor_ref2', 'Actor_ref3']
