# TODO

## Overhaul:

- [X] Remove separate process for experiment as it is obsolete now.
- [X] Clean up the repo.
- [X] Use CPU times instead of CPU percentage, per step instead of over the total process
- [ ] Improve memory profiler. Maybe it helps if we store everything in variables. 
      Current zero-measurement could be explained by the usage of the stack instead of memory.
- [ ] Only measure network traffic which is not directly related to storage size

    - [X] Data update
    - [X] Policy update
    - [ ] Not relevant: Attribute authority information request (name + attributes)
    - [ ] Location/meta share with doctor
    - [X] Update keys (for TAAC)
    - [ ] Key update (ciphertext update keys, key update keys)
    
- [X] Update keys in file storage -> are in network
- [X] Update keys: over all keys or just a few? -> all keys
- [X] User secret keys in storage are about twice the size of the keygen result. -> There are two authorities :P
- [ ] CPU times is not over the same code, but also includes file io. That is why it is higher than profile times

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
 