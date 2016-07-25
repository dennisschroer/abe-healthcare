from functools import reduce

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
    """
    util = SecretUtil(group, verbose=False)
    parsed_policy = util.createPolicy(policy)
    attribute_list = util.getAttributeList(parsed_policy)

    return reduce(
        lambda p, attribute: p.replace(attribute, add_time_period_to_attribute(attribute, time_period)),
        attribute_list,
        policy)


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
    The access policy is assumed to be in CNF, see https://en.wikipedia.org/wiki/Conjunctive_normal_form
    :param policy: The policy to translate
    :return:
    >>> group = PairingGroup('SS512')
    >>> util = SecretUtil(group, verbose=False)
    >>> policy = util.createPolicy('(ONE AND THREE) OR (TWO AND FOUR)')
    >>> translated = translate_policy_to_access_structure(policy)
    >>> translated == [['ONE', 'THREE'], ['TWO', 'FOUR']]
    True
    """
    if policy.type == OpType.OR:
        return translate_policy_to_access_structure(
            policy.getLeft()) + translate_policy_to_access_structure(policy.getRight())
    elif policy.type == OpType.AND:
        left_translated = translate_policy_to_access_structure(policy.getLeft())
        left = left_translated if policy.getLeft().type == OpType.AND else [left_translated]
        right_translated = translate_policy_to_access_structure(policy.getRight())
        right = right_translated if policy.getRight().type == OpType.AND else [right_translated]
        return left + right
    else:
        return [policy.getAttributeAndIndex()]
