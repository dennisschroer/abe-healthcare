import click as click

from client.user_client import UserClient


@click.group()
def cli():
    pass

@click.command()
@click.argument('name')
def setup(name):
    client = UserClient(name)
    pass



if __name__ == '__main__':
    cli.add_command(setup)
    cli()
