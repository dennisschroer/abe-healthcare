from os import urandom, makedirs, path


class RandomFileGenerator(object):
    """
    Generator for generating files with random content of the given size.
    """
    block_size = 4 * 1024

    @staticmethod
    def generate(size, amount, output_path='data/random', skip_if_exists=False, verbose=False) -> None:
        """
        Generate the given amount of files of the given size. The file names will have the format {size}-{number},
        where {size} is replaced by the given size and {number} by the number of the file. The first file has number 0.
        :param size: The size of the generated files.
        :param amount: The required amount of files to be generated.
        :param output_path: The path in which the files should be generated.
        :param skip_if_exists: Skip the generation when the files already exist.
        :param verbose: If true, print debug information.
        """
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
                    if verbose and (j % 100) == 99:
                        print("Block %d of %d" % (j + 1, number_of_blocks))
                    f.write(urandom(RandomFileGenerator.block_size))
                # Write the remainder
                f.write(urandom(size % RandomFileGenerator.block_size))
