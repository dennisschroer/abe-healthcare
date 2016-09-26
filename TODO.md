# TODO

## Connections:
- [X] ~~secret keys request (keygen) + response~~
- [X] ~~public keys request + response~~
- [X] ~~create record + response~~
- [X] ~~update record~~
- [X] ~~update policy~~
- [ ] location/meta share with 2nd user
- [X] ~~fetch record + response~~
- [ ] update keys (from authorities to users, if possible)

## Other
- [ ] Contribution in introduction
- [ ] Measurements: setup vs encryption/decryption
- [X] ~~Export all measurement in a helpful format~~
- [X] Differentiate between time required for symmetric and ab encryption
- [X] ~~Run each experiment in a subprocess to enable CPU usage determination~~
- [X] ~~<> Store all keys in order to measure storage costs~~
    - [X] ~~Client: owner keys~~
    - [X] ~~Client: registration data~~
    - [X] ~~Client: secret keys~~
    - [X] ~~Attribute authority: attribute public/private~~
    - [X] ~~Central authority: Global parameters~~
- [ ] [?] Encrypt as a stream, instead of all in memory (see issue 2 of charm).
- [ ] Test experiments
- [X] ~~RD13Implementation seems to have an authority attributes storage size of 6 bytes. This is most probably incorrect :(~~
- [X] ~~Measure one factor at a time~~ (Better testing required)
- [X] ~~<> Fix pickle_serializer.public_keys for TAAC12~~
- [ ] Only do encryption and decryption on raspberry: mobile is not going to be an authority
- [ ] in dacmacs: make decryption_keys part of decryption as it is required for each decryption?
    - [ ] This leaves only TAAC to have decryption keys (per time period)
 