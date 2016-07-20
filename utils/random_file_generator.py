from os import urandom, makedirs, path


class RandomFileGenerator(object):
    block_size = 1024 * 1024

    @staticmethod
    def clear(output_path='data/random'):
        pass

    @staticmethod
    def generate(size, amount, output_path='data/random', debug=False):
        if not path.exists(output_path):
            makedirs(output_path)
        for i in range(0, amount):
            with open(path.join(output_path, '%i-%i' % (size, i)), 'wb') as f:
                if debug:
                    print("Generating %s" % path.join(output_path, '%i-%i' % (size, i)))
                # We write in blocks of 1 kb
                for j in range(0, size // RandomFileGenerator.block_size):
                    f.write(urandom(RandomFileGenerator.block_size))
                # Write the remainder
                f.write(urandom(size % RandomFileGenerator.block_size))
