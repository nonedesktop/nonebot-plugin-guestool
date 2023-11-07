from typing import Any, Dict, List, Literal, Optional, Tuple, Type, Union
from uuid import uuid4
from weakref import WeakValueDictionary

from nonebot import get_driver, logger
from nonebot.internal.matcher import Matcher, matchers
from nonebot.internal.rule import Rule
from nonebot.matcher import MatcherManager
from nonebot.rule import (
    CommandRule,
    EndswithRule,
    FullmatchRule,
    KeywordsRule,
    RegexRule,
    StartswithRule,
    ToMeRule,
)
from pydantic import BaseModel

from nonebot_plugin_guestool.utils import model_dispatch

from ..exceptions import RuleCreateError, RuleParseError
from ..typing import AllMatchTypes

driver = get_driver()
matcher_ids: WeakValueDictionary[str, Type[Matcher]] = WeakValueDictionary()

_matcher_orig_setitem = MatcherManager.__setitem__


def _patch_matcher_setitem(self: MatcherManager, key: int, value: List[Type[Matcher]]) -> None:
    _matcher_orig_setitem(self, key, value)
    for ma in value:
        if ma in matcher_ids.values():
            continue
        matcher_ids[str(uuid4())] = ma


@driver.on_startup
async def matcher_mkid() -> None:
    for mas in matchers.values():
        for ma in mas:
            matcher_ids[str(uuid4())] = ma
    MatcherManager.__setitem__ = _patch_matcher_setitem
    logger.trace("Patched 'MatcherManager' to listen matcher creation")


class RuleInfo(BaseModel):
    match_type: AllMatchTypes
    common_match: Optional[Tuple[str, ...]] = None
    ignore_case: Optional[bool] = None
    commands: Optional[Tuple[Tuple[str, ...], ...]] = None
    force_cmd_whitespace: Optional[bool] = None
    regex: Optional[str] = None
    regex_flags: int = 0
    restrict_to_me: bool = False


class CommonMatchRuleInfo(BaseModel):
    match_type: Literal["startswith", "endswith", "fullmatch", "keywords"]
    common_match: Tuple[str, ...]
    ignore_case: bool = False
    restrict_to_me: bool = False

    def build_matcher_rule(self) -> Rule:
        if self.match_type == "startswith":
            rule = StartswithRule(self.common_match, self.ignore_case)
        elif self.match_type == "endswith":
            rule = EndswithRule(self.common_match, self.ignore_case)
        elif self.match_type == "fullmatch":
            rule = FullmatchRule(self.common_match, self.ignore_case)
        elif self.match_type == "keywords":
            rule = KeywordsRule(*self.common_match)
        else:
            raise RuleCreateError(f"Invalid match_type {self.match_type!r}")
        
        if self.restrict_to_me:
            return Rule(rule, ToMeRule())
        return Rule(rule)


class CommandRuleInfo(BaseModel):
    match_type: Literal["command"]
    commands: List[Tuple[str, ...]]
    force_cmd_whitespace: bool = False
    restrict_to_me: bool = False

    def build_matcher_rule(self) -> Rule:
        if self.match_type == "command":
            rule = CommandRule(self.commands, self.force_cmd_whitespace)
        else:
            raise RuleCreateError(f"Invalid match_type {self.match_type!r}")
        
        if self.restrict_to_me:
            return Rule(rule, ToMeRule())
        return Rule(rule)


class RegexRuleInfo(BaseModel):
    match_type: Literal["regex"]
    regex: str
    regex_flags: int = 0
    restrict_to_me: bool = False

    def build_matcher_rule(self) -> Rule:
        if self.match_type == "regex":
            rule = RegexRule(self.regex, self.regex_flags)
        else:
            raise RuleCreateError(f"Invalid match_type {self.match_type!r}")
        
        if self.restrict_to_me:
            return Rule(rule, ToMeRule())
        return Rule(rule)


ValidRuleInfo = Union[CommonMatchRuleInfo, CommandRuleInfo, RegexRuleInfo]


def _validate_match_type(matcher: Type[Matcher], ctx: Dict[str, Any], _ct: AllMatchTypes) -> None:
    if (_mt := ctx.setdefault("match_type", _ct)) != _ct:
        raise RuleParseError(f"Conflict match type {_mt!r} (against {_ct!r}) in {matcher!r}")


@model_dispatch(CommonMatchRuleInfo, CommandRuleInfo, RegexRuleInfo)
def extract_matcher_rule_info(matcher: Type[Matcher]) -> RuleInfo:
    kwds = {}
    for sub in matcher.rule.checkers:
        sr = sub.call
        if isinstance(sr, StartswithRule):
            _validate_match_type(matcher, kwds, "startswith")
            kwds.setdefault("common_match", ())
            kwds["common_match"] += sr.msg
            kwds["ignore_case"] = sr.ignorecase
        elif isinstance(sr, EndswithRule):
            _validate_match_type(matcher, kwds, "endswith")
            kwds.setdefault("common_match", ())
            kwds["common_match"] += sr.msg
            kwds["ignore_case"] = sr.ignorecase
        elif isinstance(sr, FullmatchRule):
            _validate_match_type(matcher, kwds, "fullmatch")
            kwds.setdefault("common_match", ())
            kwds["common_match"] += sr.msg
            kwds["ignore_case"] = sr.ignorecase
        elif isinstance(sr, KeywordsRule):
            _validate_match_type(matcher, kwds, "keywords")
            kwds.setdefault("common_match", ())
            kwds["common_match"] += sr.keywords
        elif isinstance(sr, CommandRule):
            _validate_match_type(matcher, kwds, "command")
            kwds["commands"] = sr.cmds
        elif isinstance(sr, RegexRule):
            _validate_match_type(matcher, kwds, "regex")
            kwds["regex"] = sr.regex
            kwds["regex_flags"] = sr.flags
        elif isinstance(sr, ToMeRule):
            kwds["restrict_to_me"] = True
    return RuleInfo(**kwds)


class MatcherData(BaseModel):
    plugin_name: str
    module_name: str
    type: str
    rule: ValidRuleInfo
    priority: int
    block: bool


def update_priority(ma: Type[Matcher], after: int) -> None:
    before = ma.priority
    if before not in matchers or ma not in matchers[before]:
        logger.warning(
            f"{ma!r} not included in priority {before}, "
            f"cannot move to priority {after}"
        )
        return
    if before == after:
        logger.info("priority not changed, skipped")
        return
    matchers.setdefault(after, [])
    matchers[after].append(ma)
    matchers[before].remove(ma)
    ma.priority = after
    logger.info(f"Updated the priority of {ma!r} ({before} -> {after})")
    if not matchers[before]:
        del matchers[before]
        logger.trace(f"Cleaned up unused priority {before}")


def hack_matcher(ma: Type[Matcher], ch: MatcherData) -> None:
    ma.type = ch.type
    ma.rule = ch.rule.build_matcher_rule()
    update_priority(ma, ch.priority)
    ma.block = ch.block
    logger.info(f"Hacked into {ma!r} with {ch!r}")


def hack_matcher_by_id(id: str, ch: MatcherData) -> None:
    return hack_matcher(matcher_ids[id], ch)