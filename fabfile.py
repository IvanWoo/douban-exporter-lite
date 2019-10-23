from fabric import task, Connection


def run(c, cmd):
    c.run(cmd, replace_env=False, echo=True)


@task
def freeze(c):
    run(c, "python setup.py release")
    run(c, "rm -f requirements.txt")
    run(c, "pip-compile -f dist --output-file requirements.txt")
