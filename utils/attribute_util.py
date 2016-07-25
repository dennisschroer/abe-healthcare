from functools import reduce
from typing import Callable, Any

from charm.toolbox.node import BinNode, OpType
from charm.toolbox.pairinggroup import PairingGroup
from charm.toolbox.secretutil import SecretUtil

ATTRIBUTE_TIME_FORMAT = '%d%%%s'


def add_time_periods_to_policy(policy: str, time_period: int, group: PairingGroup) -> str:
    """
    Update the policy to a policy where the attribute have the time period embedded.
    :param policy: The policy to update.
    :param time_period: The time period to embed.
    :param group:
    :return: The policy with the time period embedded.
    >>> group = PairingGroup('SS512')
    >>> add_time_periods_to_policy("STUDENT@UT", 2, group) == "2%STUDENT@UT"
    True
    >>> add_time_periods_to_policy("STUDENT@UT and TUTOR@VU", 2, group) == "2%STUDENT@UT and 2%TUTOR@VU"
    True
    >>> add_time_periods_to_policy("(STUDENT@UT and TUTOR@VU) or (FOO@BAR and (TEST@TROLL or A@B))", 5611315, group) \
    == "(5611315%STUDENT@UT and 5611315%TUTOR@VU) or (5611315%FOO@BAR and (5611315%TEST@TROLL or 5611315%A@B))"
    True
    >>> add_time_periods_to_policy(\
    "ADMINISTRATION@INSURANCE or (DOCTOR@NDB and REVIEWER@INSURANCE) or (RADIOLOGIST@NDB and REVIEWER@INSURANCE)" == \
    "1%ADMINISTRATION@INSURANCE or (1%DOCTOR@NDB and 1%REVIEWER@INSURANCE) or (1%RADIOLOGIST@NDB and 1%REVIEWER@INSURANCE)"
    True
    """
    util = SecretUtil(group, verbose=False)
    parsed_policy = util.createPolicy(policy)
    attributes = list_attributes(parsed_policy)

    return reduce(
        lambda p, attribute: p.replace(attribute, add_time_period_to_attribute(attribute, time_period)),
        attributes,
        policy)


def list_attributes(tree):
    return walk_tree(tree,
              lambda node, value: value.append(node.getAttribute()) or value if node.type == OpType.ATTR and node.getAttribute() not in value else value, [])


def walk_tree(tree: BinNode, function: Callable[[BinNode, Any], Any], value: Any):
    value = function(tree, value)
    left = tree.getLeft()
    right = tree.getRight()
    if left:
        value = walk_tree(left, function, value)
    if right:
        value = walk_tree(right, function, value)
    return value


def add_time_period_to_attribute(attribute: str, time_period: int) -> str:
    """
    Embed the time period in the attribute.
    :param attribute: The attribute.
    :param time_period: The time period to embed.
    :return: The attribute with the time period embedded
    >>> add_time_period_to_attribute("STUDENT", 2) == "2%STUDENT"
    True
    >>> add_time_period_to_attribute("STUDENT@UT", 2) == "2%STUDENT@UT"
    True
    """
    return ATTRIBUTE_TIME_FORMAT % (time_period, attribute)


def translate_policy_to_access_structure(policy: BinNode):
    """
    Translate an access policy to an access structure.
    Example: (ONE AND THREE) OR (TWO AND FOUR) is translated to
                [['ONE', 'THREE'], ['TWO', 'FOUR']]
    The access policy is assumed to be in DNF, see https://en.wikipedia.org/wiki/Disjunctive_normal_form
    :param policy: The policy to translate
    :return:
    >>> group = PairingGroup('SS512')
    >>> util = SecretUtil(group, verbose=False)
    >>> policy = util.createPolicy('(ONE AND THREE) OR (TWO AND FOUR)')
    >>> translated = translate_policy_to_access_structure(policy)
    >>> translated == [['ONE', 'THREE'], ['TWO', 'FOUR']]
    True
    >>> policy = util.createPolicy('ONE')
    >>> translated = translate_policy_to_access_structure(policy)
    >>> translated == [['ONE']]
    True
    >>> policy = util.createPolicy('(ONE AND THREE) OR (TWO AND FOUR)')
    >>> translated = translate_policy_to_access_structure(policy)
    >>> translated == [['ONE']]
    True
    """
    if policy.type == OpType.OR:
        left = translate_policy_to_access_structure(policy.getLeft())
        right = translate_policy_to_access_structure(policy.getRight())
        return left + right
    elif policy.type == OpType.AND:
        left = translate_policy_to_access_structure(policy.getLeft())
        right = translate_policy_to_access_structure(policy.getRight())
        return [left[0] + right[0]]
    else:
        return [[policy.getAttribute()]]
