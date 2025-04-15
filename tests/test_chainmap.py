from collections import ChainMap
from dataclasses import dataclass
from typing import Any

from mashumaro import DataClassDictMixin


@dataclass
class Opt1(DataClassDictMixin):
    a1: str


@dataclass
class MyConfig(DataClassDictMixin):
    opt1: Opt1
    opt2: str


def test_chainmap():
    global_config: dict[str, Any] = {"opt1": {"a1": "global_opt"}, "opt2": "global"}
    user_config = {"opt1": {"a1": "user_opt"}, "opt2": None}
    chainmap = ChainMap(user_config, global_config)
    assert chainmap["opt1"] == {"a1": "user_opt"}
    config = MyConfig.from_dict(chainmap)
    assert config.opt1.a1 == "user_opt"
