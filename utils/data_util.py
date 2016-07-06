

def pad_data_pksc5(data, block_size):
    """
    Pads data with additonal bytes containing the length of the padding.
    :param data: The data to pad
    :param block_size: The block size to pad to
    :return: The data padded according to PKCS5/PKCS7
    >>> pad_data_pksc5(bytes([0xaa, 0xbb, 0xcc, 0xdd, 0xee]), 8) == bytes([0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0x03, 0x03, 0x03])
    True
    >>> pad_data_pksc5(bytes([0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee]), 8) == bytes([0x77, 0x88, 0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08])
    True
    >>> pad_data_pksc5(b'Hello world', 8) == b'Hello World\x05\x05\x05\x05\x05'
    True
    """
    return data + bytes([block_size - (len(data) % block_size)] * (block_size - (len(data) % block_size)))
