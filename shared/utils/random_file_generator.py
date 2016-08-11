from os import urandom, makedirs, path


class RandomFileGenerator(object):
    block_size = 1024 * 1024

    @staticmethod
    def clear(output_path='data/random'):
        pass

    @staticmethod
    def generate(size, amount, output_path='data/random', skip_if_exists=False, verbose=False):
        if not path.exists(output_path):
            makedirs(output_path)
        for i in range(0, amount):
            if skip_if_exists and path.exists(path.join(output_path, '%i-%i' % (size, i))):
                continue
            with open(path.join(output_path, '%i-%i' % (size, i)), 'wb') as f:
                if verbose:
                    print("Generating %s" % path.join(output_path, '%i-%i' % (size, i)))
                number_of_blocks = size // RandomFileGenerator.block_size
                for j in range(0, number_of_blocks):
                    if verbose and (j % 100) == 0:
                        print("Block %d of %d" % (j + 1, number_of_blocks))
                    f.write(urandom(RandomFileGenerator.block_size))
                # Write the remainder
                f.write(urandom(size % RandomFileGenerator.block_size))
