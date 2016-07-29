import pickle
from typing import Any

from charm.toolbox.pairinggroup import PairingGroup
from shared.implementations.public_key.base_public_key import BasePublicKey
from shared.model.types import AbeEncryption
from shared.model.records.data_record import DataRecord




class BaseSerializer(object):
    def __init__(self, group: PairingGroup) -> None:
        self.group = group

    def serialize_abe_ciphertext(self, ciphertext: AbeEncryption) -> Any:
        """
        Serialize the ciphertext resulting form an attribute based encryption to an object which can be pickled.

        This is required because by default, instances of pairing.Element can not be pickled but have to be serialized.
        :return: An object, probably a dict, which can be pickled
        """
        raise NotImplementedError()

    def deserialize_abe_ciphertext(self, dictionary: Any) -> AbeEncryption:
        """
        Deserialize a (pickleable) dictionary back to a (non-pickleable) ciphertext.

        :return: The deserialized ciphertext.
        """
        raise NotImplementedError()



    def serialize_global_scheme_parameters(self, scheme_parameters):
        raise NotImplementedError()

    def attribute_replacement(self, dict: dict, keyword: str) -> int:
        """
        Determine a shorter identifier for the given keyword, and store it in the dict. If a keyword is already
        in the dictionary, the existing replacement identifier is used.
        :param dict: The dictionary with existing replacements.
        :param keyword: The keyword to replace.
        :return: int The replacement keyword. The dict is also updated.

        >>> i = BaseSerializer(None)
        >>> d = dict()
        >>> a = i.attribute_replacement(d, 'TEST123')
        >>> b = i.attribute_replacement(d, 'TEST123')
        >>> c = i.attribute_replacement(d, 'TEST')
        >>> a == b
        True
        >>> b == c
        False
        >>> d[a]
        'TEST123'
        >>> d[b]
        'TEST123'
        >>> d[c]
        'TEST'
        """
        for (key, value) in dict.items():
            if value == keyword:
                # Already in the dictionary
                return key
        # Not in dict
        key = len(dict)
        dict[key] = keyword
        return key

    def undo_attribute_replacement(self, dict: dict, replacement: int) -> str:
        """
        Undo the attribute replacement as result from the attribute replacement.
        :param dict: The dictionary with the replacements.
        :param replacement: The replacement to revert to the original keyword.
        :return: The original keyword.

        >>> i = BaseSerializer(None)
        >>> d = dict()
        >>> a = i.attribute_replacement(d, 'TEST123')
        >>> b = i.attribute_replacement(d, 'TEST')
        >>> i.undo_attribute_replacement(d, a) == 'TEST123'
        True
        >>> i.undo_attribute_replacement(d, b) == 'TEST'
        True
        >>> i.undo_attribute_replacement(d, 123)
        Traceback (most recent call last):
        ...
        KeyError: 123
        """
        return dict[replacement]
