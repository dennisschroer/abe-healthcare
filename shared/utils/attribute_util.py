from functools import reduce
from typing import Union, Callable, Any

# noinspection PyPackageRequirements
import boolean
# noinspection PyPackageRequirements
from boolean import AND
# noinspection PyPackageRequirements
from boolean import OR
# noinspection PyPackageRequirements
from boolean import Symbol

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
    "ADMINISTRATION@INSURANCE or (DOCTOR@NDB and REVIEWER@INSURANCE) or (RADIOLOGIST@NDB and REVIEWER@INSURANCE)", 1, group) == \
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
                     lambda node, value: value.append(
                         node.getAttribute()) or value if node.type == OpType.ATTR and node.getAttribute() not in value else value,
                     [])


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


def translate_policy_to_access_structure(policy: str) -> list:
    """
    Translate an access policy to an access structure.
    Example: (ONE AND THREE) OR (TWO AND FOUR) is translated to
                [['ONE', 'THREE'], ['TWO', 'FOUR']]
    :param policy: The policy to translate
    :return:
    >>> policy = '(ONE AND THREE) OR (TWO AND FOUR)'
    >>> translated = translate_policy_to_access_structure(policy)
    >>> equal_access_structures(translated, [['ONE', 'THREE'], ['TWO', 'FOUR']])
    True
    >>> policy = 'ONE'
    >>> translated = translate_policy_to_access_structure(policy)
    >>> equal_access_structures(translated, [['ONE']])
    True
    >>> policy = '(ONE AND THREE) OR (TWO AND FOUR AND FIVE) OR (SEVEN AND SIX)'
    >>> translated = translate_policy_to_access_structure(policy)
    >>> equal_access_structures(translated, [['ONE', 'THREE'], ['TWO', 'FOUR', 'FIVE'], ['SEVEN', 'SIX']])
    True
    >>> policy = '(ONE OR THREE) AND (TWO OR FOUR)'
    >>> translated = translate_policy_to_access_structure(policy)
    >>> equal_access_structures(translated, [['ONE', 'TWO'], ['ONE', 'FOUR'], ['THREE', 'TWO'], ['THREE', 'FOUR']])
    True
    """
    algebra = boolean.BooleanAlgebra()
    dnf = algebra.dnf(algebra.parse(policy.replace('@', '::')))
    return dnf_algebra_to_access_structure(dnf)


def dnf_algebra_to_access_structure(policy: Union[OR, AND, Symbol]) -> list:
    """
    Transform a DNF algebra formular to an access structure.
    :param policy: The policy to transform
    :return: The access structure

    >>> algebra = boolean.BooleanAlgebra()
    >>> policy = algebra.parse('(ONE AND THREE) OR (TWO AND FOUR AND FIVE) OR (SEVEN AND SIX)')
    >>> translated = dnf_algebra_to_access_structure(policy)
    >>> equal_access_structures(translated, [['ONE', 'THREE'], ['TWO', 'FOUR', 'FIVE'], ['SEVEN', 'SIX']])
    True
    """
    if isinstance(policy, OR):
        return reduce(lambda base, sub_policy: base + dnf_algebra_to_access_structure(sub_policy), policy.args, [])
    elif isinstance(policy, AND):
        return [reduce(lambda base, sub_policy: base + dnf_algebra_to_access_structure(sub_policy)[0], policy.args, [])]
    elif isinstance(policy, Symbol):
        return [[policy.obj.replace('::', '@')]]


def equal_access_structures(first_access_structure, other_access_structure):
    """
    Compare access structures for equality, independent of order
    :param first_access_structure:
    :param other_access_structure:
    :return:
    >>> equal_access_structures([[1]], [[1]])
    True
    >>> equal_access_structures([[1,2]], [[1,2]])
    True
    >>> equal_access_structures([[1,2]], [[2,1]])
    True
    >>> equal_access_structures([[1,2], [3,4]], [[4,3], [1,2]])
    True
    >>> equal_access_structures([[1,2]], [[1,3]])
    False
    >>> equal_access_structures([[1,2]], [[1,2,3]])
    False
    >>> equal_access_structures([[1,2]], [[1,2], [3,4]])
    False
    """
    return set(map(lambda x: frozenset(x), first_access_structure)) == \
           set(map(lambda x: frozenset(x), other_access_structure))
