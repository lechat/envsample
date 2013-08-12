#!multiconf

from multiconf.envs import EnvFactory
from multiconf import ConfigRoot, ConfigItem, ConfigBuilder
from multiconf.decorators import nested_repeatables, repeat, required, named_as

@nested_repeatables('cloud_servers, jenkins, apache')
@required('git')
class Project(ConfigRoot):
    def __init__(self, selected_env, name, valid_envs, **attr):
        super(Project, self).__init__(selected_env=selected_env, name=name,
                                      valid_envs=valid_envs, **attr)

    def render(self):
        # for all items within config:
        # collect result of their own render() function
        pass

@named_as('cloud_servers')
@repeat()
class CloudServer(ConfigItem):
    def __init__(self, host_name, server_num):
        print 'DEBUG: in CloudServer.__init__ host_name=', host_name
        super(CloudServer, self).__init__(host_name=host_name,
                                          server_num=server_num)
        print 'DEBUG: in CloudServer.__init__ self.host_name=', self.host_name

class CloudServers(ConfigBuilder):
    '''
    This is builder - it will insert into config multiple objects
    if type CloudServer and will calculate hostname for each
    '''
    def __init__(self, host_name, num_servers):
        super(CloudServers, self).__init__(host_name=host_name,
                                           num_servers=num_servers)

    def build(self):
        for server_num in xrange(1, self.num_servers+1):
            cs = CloudServer(host_name='%s%s' % (self.host_name, server_num),
                             server_num=server_num)
            print 'DEBUG: cs.host_name=%s' % cs.host_name

@named_as('git')
class GitRepo(ConfigItem):
    def __init__(self, origin, branch, branches_mask):
        super(GitRepo, self).__init__(origin=origin, branch=branch,
                                      branches_mask=branches_mask)

@named_as('jenkins')
@required('nodes, view')
@repeat()
class Jenkins(ConfigItem):
    def __init__(self, num_nodes, base_port=0):
        super(Jenkins, self).__init__(num_nodes=num_nodes, base_port=base_port)

@named_as('nodes')
class Nodes(ConfigItem):
    def __init__(self, hosts):
        super(Nodes, self).__init__(hosts=hosts)

@named_as('view')
@nested_repeatables('sub_view')
class NestedView(ConfigItem):
    def __init__(self, name):
        super(NestedView, self).__init__(name=name)

@named_as('sub_view')
@repeat()
class JobsView(ConfigItem):
    def __init__(self, name):
        super(JobsView, self).__init__(name=name)

class Jobs(ConfigItem):
    def __init__(self, slaves=None):
        super(Jobs, self).__init__(slaves=slaves)

class ProjectJobs(Jobs):
    pass

class RepositoryJobs(Jobs):
    pass

@named_as('apache')
@repeat()
class Apache(ConfigItem):
    def __init__(self, base_port, nodes):
        super(Apache, self).__init__(base_port=base_port, nodes=nodes)

class Database(ConfigItem):
    def __init__(self, name):
        super(Database, self).__init__(name=name)

# Define environments

# Use EnvFactory() to create environment or group of environments
ef = EnvFactory()

# We have five environments and we define them here
devlocal = ef.Env('devlocal')   # Local dev box
dev = ef.Env('dev')           # Dev build box
cloud = ef.Env('cloud')       # Cloud
prod = ef.Env('prod')

# Grouping environments per their roles
g_dev = ef.EnvGroup('g_dev', devlocal, dev, cloud)
g_prod = ef.EnvGroup('g_prod', prod)


# This function is used to describe all environments and return an instantiated environment
# configuration for environment with name 'env_name', which is passed as parameter
def conf(env_name):
    env = ef.env(env_name)

    with Project(env, 'SampleProject', [g_dev, g_prod]) as project:

        # CloudServers is a multiconf builder - it will not be present in
        # configuration. Instead there will be CloudServer objects based on
        # num_servers parameter
        with CloudServers(host_name='something', num_servers=0) as cloud_servers:
            cloud_servers.setattr('num_servers', devlocal=1, dev=2, cloud=4)

        # GitRepo is set to be a required element of a project
        # Try to comment out this declaration and see what happens
        with GitRepo(origin='git@github.com:lechat/envsample.git',
                     branch='master', branches_mask='fb_[0-9]*$') as git:
            git.setattr('branch', g_dev='develop')

        with Jenkins(num_nodes=0) as jenkins:
            jenkins.setattr('num_nodes', g_dev=2)
            jenkins.setattr('base_port', g_dev=8080)
            # Nodes is a builder too
            jenkins_nodes = Nodes(hosts=cloud_servers)
            with NestedView(project.name) as top_view:
                with JobsView('%s_branches' % project.name) as jw1:
                    ProjectJobs(jenkins_nodes)
                with JobsView('%s_common' % project.name) as jw1:
                    RepositoryJobs()

        with Apache(base_port=80, nodes=cloud_servers) as apache:
            apache.setattr('base_port', g_dev=18000)

        with Database('%s_db' % project.name) as db:
            db.setattr('name', g_dev='%s_dev_db' % project.name)

    return project

config = conf('devlocal')
print config
assert(config.name=='SampleProject')
# Check that we only have one cloud server in devlocal
assert(len(config.cloud_servers)==1)
print config.cloud_servers
cloud_server = config.cloud_servers.values()[0]
assert(isinstance(cloud_server, CloudServer))
assert(cloud_server.host_name == 'something1')
