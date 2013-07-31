import imp

# This is Salt renderer's call
def render(template, env='', sls='', argline='', context=None, **kws):
    config = imp.new_module(sls)

    project = config.conf(env)

    return project.render()

