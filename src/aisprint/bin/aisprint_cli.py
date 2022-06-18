import click
import pkg_resources
from cookiecutter.main import cookiecutter

from ..design import run_design 

@click.group()
def aisprint_cli():
    pass

@click.command()
@click.option("--application_name", help="Name of the new AI-SPRINT application.", type=str, required=False)
def new_application(application_name):
    # NOTE: maybe better on repository?
    no_input = True if application_name else False
    extra_context = {'application_name': application_name} if application_name else {}
    template_file = pkg_resources.resource_filename('aisprint', 'application_template/application_template.zip')
    cookiecutter(template_file, no_input=no_input, extra_context=extra_context)
    print("DONE. New AI-SPRINT application '{}' has been created.".format(application_name))

@click.command()
@click.option("--application_dir", help="Path to the AI-SPRINT application.", required=True)
def design(application_dir):
    run_design(application_dir)
    print("DONE. Application designs have been generated.") 

aisprint_cli.add_command(design)
aisprint_cli.add_command(new_application)

if __name__ == '__main__':
    aisprint_cli()
