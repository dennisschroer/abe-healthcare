import unittest

from charm.core.math.pairing import GT
from exception.policy_not_satisfied_exception import PolicyNotSatisfiedException
from implementations.base_implementation import BaseImplementation


class ImplementationBaseTestCase(unittest.TestCase):
    # noinspection PyUnusedLocal,PyPep8Naming
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject = None  # type: BaseImplementation

    def ske_encrypt_decrypt(self):
        key = b'a' * self.subject.ske_key_size()
        for m in [b'Hello world', lorem]:
            c = self.subject.ske_encrypt(m, key)
            self.assertNotEqual(c, m)
            d = self.subject.ske_decrypt(c, key)
            self.assertEqual(m, d)
            r = self.subject.ske_decrypt(c, b'b' * self.subject.ske_key_size())
            self.assertNotEqual(m, r)

    def pke_sign_verify(self):
        key = self.subject.pke_generate_key_pair(1024)
        for m in [b'Hello world', lorem]:
            s = self.subject.pke_sign(key, m)
            self.assertNotEqual(s, m)
            self.assertTrue(self.subject.pke_verify(key, s, m))

    def setup_abe(self):
        # Setup authorities
        self.ca = self.subject.create_central_authority()
        self.ma1 = self.subject.create_attribute_authority('A1')
        self.ma2 = self.subject.create_attribute_authority('A2')
        self.global_parameters = self.ca.setup()
        self.ma1.setup(self.ca, ['ONE@A1', 'TWO@A1'])
        self.ma2.setup(self.ca, ['THREE@A2', 'FOUR@A2'])

        # Setup keys
        self.public_keys = self.subject.merge_public_keys({self.ma1.name: self.ma1, self.ma2.name: self.ma2})
        self.valid_secret_keys = []  # type: list
        self.invalid_secret_keys = []  # type:list

        # Just enough secret keys
        self.secret_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.secret_keys, self.ma1.keygen('alice', ['ONE@A1'], 1))
        self.subject.update_secret_keys(self.secret_keys, self.ma2.keygen('alice', ['THREE@A2'], 1))
        self.valid_secret_keys.append(self.secret_keys)

        # All secret keys
        self.all_secret_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.all_secret_keys, self.ma1.keygen('alice', ['ONE@A1', 'TWO@A1'], 1))
        self.subject.update_secret_keys(self.all_secret_keys, self.ma2.keygen('alice', ['THREE@A2', 'FOUR@A2'], 1))
        self.valid_secret_keys.append(self.all_secret_keys)

        # No secret keys
        self.invalid_secret_keys.append(self.subject.setup_secret_keys('alice'))

        # Not enough secret keys
        self.not_enough_secret_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.not_enough_secret_keys, self.ma1.keygen('alice', ['ONE@A1'], 1))
        self.invalid_secret_keys.append(self.not_enough_secret_keys)

        # All secret keys, but invalid time period
        self.invalid_time_keys = self.subject.setup_secret_keys('alice')
        self.subject.update_secret_keys(self.invalid_time_keys, self.ma1.keygen('alice', ['ONE@A1', 'TWO@A1'], 2))
        self.subject.update_secret_keys(self.invalid_time_keys, self.ma2.keygen('alice', ['THREE@A2', 'FOUR@A2'], 2))

        self.policy = 'ONE@A1 AND THREE@A2'

    def decryption_key(self, secret_keys, time_period: int):
        """
        Decrypt the ABE ciphertext. The method calculates decryption keys if necessary.
        :param ciphertext: The ABE ciphertext to decrypt.
        :param time_period: The time period.
        :raise exceptions.policy_not_satisfied_exception.PolicyNotSatisfiedException
        :return: The plaintext
        """
        if self.subject.decryption_keys_required:
            decryption_keys = self.subject.decryption_keys({'A1': self.ma1, 'A2': self.ma2},
                                                           secret_keys, time_period)
        else:
            decryption_keys = secret_keys
        return decryption_keys

    def encrypt_decrypt_abe(self):
        self.setup_abe()

        m = self.global_parameters.group.random(GT)

        # Encrypt message
        ciphertext = self.subject.abe_encrypt(self.global_parameters, self.public_keys, m, self.policy, 1)
        self.assertNotEqual(m, ciphertext)

        # if self.subject.decryption_keys_required:
        #    decryption_keys = self.subject.decryption_keys()

        # Attempt to decrypt
        for secret_keys in self.valid_secret_keys:
            decrypted = self.subject.abe_decrypt(self.global_parameters, self.decryption_key(secret_keys, 1), 'alice',
                                                 ciphertext)
            self.assertEqual(m, decrypted)

        for secret_keys in self.invalid_secret_keys:
            try:
                self.subject.abe_decrypt(self.global_parameters, self.decryption_key(secret_keys, 1), 'alice',
                                         ciphertext)
                self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
            except PolicyNotSatisfiedException:
                pass

        try:
            self.subject.abe_decrypt(self.global_parameters, self.decryption_key(self.invalid_time_keys, 2), 'alice',
                                     ciphertext)
            self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
        except PolicyNotSatisfiedException:
            pass

    def encrypt_decrypt_abe_wrapped(self):
        self.setup_abe()

        for m in [b'Hello world', lorem]:
            # Encrypt message
            key, ciphertext = self.subject.abe_encrypt_wrapped(self.global_parameters, self.public_keys, m, self.policy,
                                                               1)
            self.assertNotEqual(m, ciphertext)

            # Attempt to decrypt the messages
            for secret_keys in self.valid_secret_keys:
                decrypted = self.subject.abe_decrypt_wrapped(self.global_parameters,
                                                             self.decryption_key(secret_keys, 1), 'alice',
                                                             (key, ciphertext))
                self.assertEqual(m, decrypted)

            for secret_keys in self.invalid_secret_keys:
                try:
                    self.subject.abe_decrypt_wrapped(self.global_parameters, self.decryption_key(secret_keys, 1),
                                                     'alice', (key, ciphertext))
                    self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
                except PolicyNotSatisfiedException:
                    pass

            try:
                self.subject.abe_decrypt_wrapped(self.global_parameters, self.decryption_key(self.invalid_time_keys, 2),
                                                 'alice', (key, ciphertext))
                self.fail("Should throw an PolicyNotSatisfiedException because of insufficient secret keys")
            except PolicyNotSatisfiedException:
                pass

    def abe_serialize_deserialize(self):
        self.setup_abe()

        m = self.global_parameters.group.random(GT)

        # Encrypt message
        ciphertext = self.subject.abe_encrypt(self.global_parameters, self.public_keys, m, self.policy, 1)

        serialized = self.subject.serialize_abe_ciphertext(ciphertext)
        self.assertIsNotNone(serialized)

        deserialized = self.subject.deserialize_abe_ciphertext(serialized)
        self.assertIsNotNone(deserialized)
        self.assertEqual(deserialized, ciphertext)


if __name__ == '__main__':
    unittest.main()

lorem = b"""
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Integer consequat sapien a lectus gravida euismod. Sed vitae nisl non odio viverra accumsan. Curabitur nisi neque, egestas sed, vulputate sit amet, luctus vitae, dolor. Cras lacus massa, sagittis ut, volutpat consequat, interdum a, nulla. Vivamus rhoncus molestie nulla. Ut porttitor turpis sit amet turpis. Nam suscipit, justo quis ullamcorper sagittis, mauris diam dictum elit, suscipit blandit ligula ante sit amet mauris. Integer id arcu. Aenean scelerisque. Sed a purus. Pellentesque nec nisl eget metus varius tempor. Curabitur tincidunt iaculis lectus. Aliquam molestie velit id urna. Suspendisse in ante ac nunc commodo placerat.

Morbi gravida posuere est. Fusce id augue. Sed facilisis, felis quis ornare consequat, neque risus faucibus dui, quis ullamcorper tellus lacus vitae felis. Phasellus ac dolor. Integer ante diam, consectetuer in, tempor vitae, volutpat in, enim. Integer diam felis, semper at, iaculis ut, suscipit quis, dolor. Vestibulum semper, velit et tincidunt vehicula, nisl risus eleifend ipsum, vel consectetuer enim dolor id magna. Praesent hendrerit urna ac lacus. Maecenas porttitor ipsum sed orci. In ac odio vel lorem tincidunt pellentesque. Nam tempor pulvinar turpis. Nunc in leo in libero ultricies interdum. Proin ut urna. Donec ultricies nunc dapibus justo. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Praesent vulputate, lectus pulvinar nonummy eleifend, sapien urna posuere metus, vel auctor risus odio eu augue. Cras vitae dolor. Phasellus dolor. Etiam enim. Donec erat felis, tincidunt quis, luctus in, faucibus at, est.

Mauris ac eros. Donec quis lacus. Nam et lacus. Mauris in orci a dolor placerat sollicitudin. Vivamus sollicitudin, nibh ac consectetuer auctor, quam massa volutpat leo, id ornare nunc nisi nec lacus. Aliquam sit amet lectus ac turpis cursus tempus. Sed sit amet purus et mi ultrices laoreet. Sed pretium. In tempor dapibus tortor. Etiam lacinia risus non dui. Duis libero arcu, convallis vel, adipiscing ut, pellentesque sit amet, metus. Nulla facilisi. Sed pharetra, urna vitae nonummy hendrerit, elit massa ultrices lacus, non suscipit enim pede ac enim. Nam arcu urna, fermentum non, lacinia ut, commodo id, nisi. Suspendisse odio urna, mollis vitae, pretium in, porta in, ligula. Fusce neque felis, posuere quis, ultrices eu, mollis a, turpis. Praesent sem urna, semper quis, sollicitudin vel, commodo sit amet, enim. Fusce semper sem vel ipsum. Vivamus et massa. Mauris pretium blandit lorem.

Nullam varius, quam eget tempus fermentum, felis massa feugiat est, ac lacinia nisi leo ac sapien. Nullam eu odio ultrices pede rutrum faucibus. Nam nonummy placerat risus. Phasellus dictum blandit tortor. Vivamus a lectus. Ut ligula nibh, sodales pellentesque, lacinia sed, luctus at, ipsum. Curabitur ornare. Sed magna erat, sagittis eget, volutpat sit amet, sodales nec, quam. In lobortis porttitor odio. Donec nunc. Donec tristique ornare eros. Mauris id urna et augue facilisis dictum.

Duis volutpat fringilla felis. Quisque mollis aliquam neque. Morbi lacinia. Vivamus non purus. Proin accumsan nunc eu pede. Phasellus adipiscing diam tempus libero. Suspendisse ornare sapien non magna. Nullam in nibh. Vestibulum consequat, quam et luctus viverra, nunc magna aliquam orci, non placerat ligula massa ac massa. Donec mi diam, adipiscing iaculis, rhoncus sit amet, venenatis sit amet, nisi. Sed iaculis, nisl vel accumsan condimentum, orci felis congue pede, nec pharetra quam ante nec ligula. Cras non massa ac ligula auctor ultrices. Maecenas enim purus, mattis ac, interdum a, suscipit eget, elit. Morbi volutpat mauris sit amet elit. Maecenas pretium, ipsum ut semper vulputate, sapien lectus tristique dui, sit amet ullamcorper massa libero ut neque. Praesent nec ante.

Pellentesque nibh erat, tristique in, dignissim nec, vehicula at, massa. Maecenas condimentum, enim quis vulputate sodales, justo tellus vulputate arcu, in luctus metus quam eget lacus. Integer accumsan, lacus auctor tempor egestas, pede odio accumsan nisl, quis commodo mauris pede vitae lacus. Ut leo. In rutrum nulla nec magna porttitor adipiscing. Donec dapibus. Maecenas magna. Nam volutpat ante vel orci. Etiam faucibus, nisl id auctor tristique, erat justo laoreet velit, ac tincidunt ante orci congue risus. Fusce elementum nisl at augue. Maecenas sapien. Maecenas eget eros vel metus accumsan venenatis. Cras id pede eget quam consequat fringilla. Aenean tempor velit eu lorem. Vivamus ac ligula. Aliquam interdum quam. Vivamus eu sapien ut est porta consequat. Morbi lacinia lacus a velit. Integer rhoncus.

Praesent accumsan cursus ante. Pellentesque odio odio, euismod vitae, pharetra quis, bibendum et, augue. Nam consectetuer. Praesent eu lorem sit amet neque euismod malesuada. Proin viverra turpis at urna. Nunc posuere pulvinar augue. Suspendisse eros tortor, rhoncus a, varius a, gravida ut, justo. Suspendisse potenti. Morbi mi. Duis iaculis arcu ac felis. Vestibulum urna tellus, facilisis nec, egestas nec, pharetra et, tellus. Donec posuere lectus ut sapien. Fusce mollis dui adipiscing sapien. Sed condimentum pede quis ipsum. Donec mauris ligula, cursus eget, hendrerit ut, tempor nec, urna. Curabitur fringilla nisl et nibh. Aliquam ut ligula vel velit dignissim porttitor. Suspendisse eget mi.

Fusce dictum turpis ac nibh. Donec pretium ipsum. Vivamus blandit ornare velit. Praesent fringilla, dolor et ullamcorper dignissim, augue lorem dignissim leo, eget interdum nibh ipsum non ligula. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos hymenaeos. Morbi quam. Proin in enim a dolor auctor imperdiet. Phasellus molestie massa a pede. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Praesent volutpat sem et tortor gravida iaculis. Quisque ornare convallis justo. Maecenas euismod ullamcorper dui. Mauris elementum dignissim libero. Sed dignissim placerat augue. Nullam consequat tellus sed eros. Nam interdum ipsum id lectus. Curabitur pretium sapien egestas augue. Maecenas sodales lectus. Proin luctus.

Integer commodo, dui ut vulputate tristique, nisl magna fringilla mauris, id ultricies nisl elit nec tellus. Sed tincidunt. Mauris fringilla ultricies purus. In hac habitasse platea dictumst. Aenean lacinia interdum mauris. Donec ante ligula, rutrum ac, condimentum nec, lobortis sed, purus. Nulla dictum, tortor sit amet egestas vulputate, ipsum tortor auctor nulla, non tempus tellus mauris quis urna. Ut pharetra tortor in purus. Morbi vel nibh nec mi cursus pretium. Duis interdum. Sed in ipsum. Aenean rutrum. Etiam placerat velit id risus. Suspendisse potenti. Pellentesque feugiat, augue eu vestibulum lobortis, dui nulla tempus sem, sit amet malesuada elit arcu in magna. Aliquam sollicitudin nibh. Fusce convallis, leo tempus scelerisque mattis, pede sem luctus diam, eu vestibulum mauris sapien quis sapien. Phasellus placerat vehicula metus. Proin sapien mi, semper vitae, ultrices vitae, aliquet eget, nisi. Integer eu quam.

Ut eget massa in est rutrum pulvinar. Sed pulvinar arcu vulputate nibh interdum tempor. Aliquam ut nulla quis arcu porta consectetuer. Pellentesque ullamcorper, felis in hendrerit facilisis, magna enim pharetra pede, vel laoreet tortor turpis quis quam. Quisque id velit non leo auctor mattis. Nam ultrices purus vehicula nisl. Vestibulum rutrum, odio a mattis venenatis, eros lorem iaculis massa, in scelerisque leo ligula vel mauris. Praesent est enim, porttitor eget, suscipit vitae, adipiscing vitae, nibh. Proin risus. Vestibulum augue urna, sagittis at, vehicula pharetra, mollis sit amet, erat.

Vivamus semper elementum ipsum. Aenean commodo, massa nec vehicula porta, nisl risus facilisis orci, sit amet placerat nibh leo quis massa. Pellentesque vestibulum massa ac magna dapibus eleifend. Pellentesque sed quam nec diam ultricies sagittis. Nullam congue erat a erat. Sed eu est et turpis adipiscing blandit. Aenean arcu lectus, pretium non, ultricies quis, ultricies et, eros. Quisque placerat dui vel dui mattis gravida. Nam felis massa, elementum eget, interdum sed, suscipit sed, massa. Ut accumsan, massa sed porttitor commodo, arcu nibh suscipit quam, at ultricies dui mauris eu mauris. Nullam metus.

Donec posuere nisi vehicula ligula. Morbi ante arcu, consectetuer tristique, ornare facilisis, vehicula aliquam, dui. Vivamus ut neque. Sed faucibus. Cras faucibus diam vitae erat. Duis quis risus vitae nunc dignissim pellentesque. Nulla facilisi. Donec semper augue eget tortor. Vivamus euismod lectus id dui. Quisque volutpat nisl eu urna. Curabitur rhoncus metus vitae augue. Mauris et dui a ipsum feugiat vestibulum. Praesent ornare. Sed quis risus a orci hendrerit facilisis. Nulla at felis. Donec scelerisque, sapien vitae dapibus interdum, felis odio commodo tortor, vitae dignissim mi ipsum in odio. Nunc blandit tempor risus. Pellentesque rhoncus urna at justo tincidunt tempor. Suspendisse luctus condimentum purus.

Cras in tellus eu felis auctor bibendum. Nullam in felis. Ut non nisl. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Aenean condimentum, augue eget cursus ornare, tortor justo sagittis neque, et congue sem mi at massa. Nunc nec erat eu odio varius bibendum. Praesent commodo molestie erat. In hac habitasse platea dictumst. Nunc fermentum magna at arcu. Morbi aliquet commodo tellus. Phasellus lorem elit, luctus ac, dapibus nec, suscipit ac, nulla. Aenean egestas pharetra tellus. Fusce quis nunc. Aliquam eu erat. Pellentesque non erat.

Maecenas massa augue, adipiscing non, viverra eget, porta eu, dui. Fusce imperdiet. Nulla facilisi. Sed sollicitudin ultrices risus. Nam nec turpis et tellus malesuada mattis. Donec elit. Integer scelerisque lacus vel magna. Curabitur euismod ornare sem. Nullam arcu arcu, eleifend et, auctor at, elementum eu, est. Aliquam vestibulum. Aliquam pretium convallis nisi. Vivamus vitae felis quis mi ornare blandit. In quis risus. In eleifend fermentum eros. Vestibulum at odio ut tellus lobortis tristique. Sed vel justo at ante aliquet blandit. Praesent dictum felis vel nulla. Suspendisse potenti. Integer pretium, lacus varius congue posuere, odio purus malesuada ante, id adipiscing justo ipsum vitae dui. Donec est risus, laoreet sed, gravida tristique, molestie sed, risus.

Phasellus sed enim sed mauris ultrices semper. Phasellus vel sem. Mauris a dui. Vivamus facilisis rutrum metus. Mauris suscipit, odio eu laoreet mattis, lacus massa placerat mi, nec eleifend magna nunc nec sem. Vivamus quam sem, condimentum a, pellentesque nec, interdum vel, orci. Fusce placerat urna ac felis. Vestibulum neque. Donec rhoncus diam eget metus. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Phasellus semper lacus quis dolor. Curabitur erat. In hac habitasse platea dictumst. Curabitur tristique. Aliquam felis. Integer ac justo. Etiam nisl nisi, sodales ac, egestas eu, accumsan a, sapien. Nam ultrices, libero et bibendum interdum, eros nulla nonummy enim, a viverra augue eros at orci. Quisque luctus, sem sed dapibus pharetra, velit dolor adipiscing nisl, vel varius lectus augue et ante.

Ut ullamcorper, arcu vitae volutpat auctor, urna erat lobortis diam, at ullamcorper nulla sapien id ante. Donec a orci quis massa viverra sagittis. Quisque pretium tortor a lectus convallis tempus. Integer aliquet. Vestibulum vitae dolor non libero imperdiet dapibus. Donec nibh. Cras blandit, pede vitae iaculis auctor, nunc sem dapibus turpis, fermentum mattis nunc massa vitae ipsum. Donec nec justo. Cras nec sem luctus tortor vehicula accumsan. Praesent facilisis magna a elit. Sed vestibulum dui nec enim. Vivamus quis erat.

Integer sollicitudin ligula a libero. In eu sem a lorem semper ultrices. Mauris adipiscing dignissim sapien. Nullam in sapien. Donec tincidunt magna sit amet augue. Donec dapibus. Sed euismod eros vel lacus. Aenean pede. Donec semper, augue nec viverra pretium, sapien enim interdum risus, vitae consequat leo turpis non dolor. Morbi tincidunt posuere quam. Vivamus nisi lectus, volutpat id, tempus eget, volutpat eget, nunc. Curabitur ipsum nunc, tincidunt sed, tempus sed, placerat eu, lacus. Aenean at sapien nec mi laoreet tincidunt.

Integer rhoncus, tellus eget eleifend ultricies, nisi lorem iaculis justo, non faucibus mauris mauris a mi. Nulla arcu quam, fringilla a, rhoncus quis, porta eu, augue. Maecenas molestie quam eget sem. Integer tristique. Duis adipiscing, risus id ullamcorper ultrices, velit lacus gravida elit, vel mollis diam lorem eget mauris. Cras sed justo id urna rutrum consectetuer. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos hymenaeos. Integer congue. Sed ante felis, blandit mattis, congue ut, fermentum ut, pede. Suspendisse libero. Mauris a dolor interdum nunc vestibulum adipiscing.

Vestibulum interdum, nisl non cursus rhoncus, felis arcu dictum dolor, at iaculis eros risus sit amet leo. Proin ac tellus a purus pellentesque pharetra. Pellentesque sit amet nibh. Cras tellus. Fusce ultrices massa a quam. Vestibulum a augue eget augue egestas ultrices. Ut porttitor auctor eros. Sed ut felis vel mauris suscipit consequat. Quisque in pede. Ut lobortis diam sit amet lectus. Donec vehicula tortor. Praesent porttitor lacus quis est ullamcorper egestas. Donec porttitor dui id metus. Donec adipiscing gravida mi. Phasellus diam mi, adipiscing sit amet, porttitor vel, suscipit id, enim. Morbi non tortor vel ante posuere malesuada. Praesent pellentesque justo. Curabitur tempus aliquet erat. In eleifend elit vel magna.

Morbi auctor tempus purus. Quisque sed risus id sem nonummy aliquet. Donec gravida, ipsum et ullamcorper consectetuer, lacus erat mollis enim, sed semper arcu sapien vitae erat. Pellentesque mattis luctus tortor. Donec elementum. Donec sagittis. Cras vel orci. Integer adipiscing. Sed placerat, nunc nec tempor pretium, nulla lectus scelerisque libero, a rhoncus tellus eros in neque. In hac habitasse platea dictumst. Praesent egestas urna rhoncus quam. Aenean hendrerit blandit arcu. Proin enim est, porttitor non, egestas at, feugiat dapibus, dolor. Mauris auctor. Donec ornare, urna vitae suscipit venenatis, pede nisi fringilla lorem, nec ultricies tortor eros eu mi. Proin porta arcu ac orci. Nullam in nunc. Mauris libero sapien, lobortis ac, fermentum sit amet, pulvinar quis, nulla. Phasellus tortor ligula, semper viverra, venenatis non, vehicula sit amet, neque.
"""
