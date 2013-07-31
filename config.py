from multiconf.envs import EnvFactory

# Define environments

# Use EnvFactory() to create environment or group of environments
ef = EnvFactory()

# We have five environments and we define them here
devlocal = ef.Env('devlocal')   # Local dev box
dev = ef.Env('dev')           # Dev build box
preprod = ef.Env('cloud')       # Cloud
prod = ef.Env('prod')

# Grouping environments per their roles
g_dev = ef.EnvGroup('g_dev', devlocal, dev, cloud)
g_prod = ef.EnvGroup('g_prod', prod)


# This function is used to describe all environments and return an instantiated environment
# configuration for environment with name 'env_name', which is passed as parameter
def conf(env_name):
    env = ef.env(env_name)

    with Project(env, 'SampleProject', [g_dev, g_prod]) as project:
        
        # CloudServers need to be a multiconf builder
        with CloudServers(host_name='something', g_prod=4) as cloud_servers:
            cloud_servers.setattr('num_servers', devlocal=0, dev=0, cloud=2)

        with Jenkins(g_prod=0) as jenkins:
            jenkins.setattr('base_port', g_dev=8080)
            # Nodes is a builder too
            with Nodes(g_prod=4, cloud_servers) as jenkins_nodes:
                jenkins_nodes.setattr('num_nodes', devlocal=1, dev=1, cloud=2)
            with NestedView(project.name) as top_view:
                with JobsView() as jw1:
                    ProjectJobs(jenkins_nodes)
                with JobsView() as jw1:
                    RepositoryJobs()

        with Apache(base_port=80, nodes=cloud_servers) as apache:
            apache.setattr('base_port', g_dev=18000)

        with Database('%s_db' % project.name) as db:
            db.seattr('name', g_dev='%s_dev_db' % project.name)

    return project   
