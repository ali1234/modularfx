import click


@click.command()
@click.argument('filename', type=click.Path(readable=True), required=False)
@click.option('-o', '--output', type=click.File('wb'), help='Start with no GUI and write sound to output.')
def main(filename, output):
    if output is not None:
        from modularfx.cli import cli
        cli(filename, output)
    else:
        from modularfx.gui import gui
        gui(filename)
