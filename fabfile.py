from fabric import task, Connection


def run(c, cmd):
    c.run(cmd, replace_env=False, echo=True)


@task
def freeze(c):
    run(c, "rm -f requirements.txt")
    run(c, "pipenv lock -r > requirements.txt")
