# TODO

## Connections:
- ~~secret keys request (keygen) + response~~
- ~~public keys request + response~~
- ~~create record + response~~
- ~~update record~~
- ~~update policy~~
- location/meta share with 2nd user
- ~~fetch record + response~~
- update keys (from authorities to users, if possible)

## Other
- Contribution in introduction
- Measurements: setup vs encryption/decryption
- ~~Export all measurement in a helpful format~~
- [?] Differentiate between time required for symmetric and ab encryption
- ~~Run each experiment in a subprocess to enable CPU usage determination~~
- ~~<> Store all keys in order to measure storage costs~~
    - ~~Client: owner keys~~
    - ~~Client: registration data~~
    - ~~Client: secret keys~~
    - ~~Attribute authority: attribute public/private~~
    - ~~Central authority: Global parameters~~
- [?] Encrypt as a stream, instead of all in memory (see issue 2 of charm).
- Test experiments
- ~~RD13Implementation seems to have an authority attributes storage size of 6 bytes. This is most probably incorrect :(~~
- ~~Measure one factor at a time~~ (Better testing required)
- ~~<> Fix pickle_serializer.public_keys for TAAC12~~