**APImetrics-Python-Client**

Command line-callable Python library that makes it easier to call APImetrics' APIs.

For use with your APImetrics monitoring service. Please sign up at http://client.apimetrics.io and create an API key at https://client.apimetrics.io/settings/api-key

**Installation**

Create a settings file at ``/etc/APImetrics`` or ``~/.APImetrics`` or locally (specify it with the ``-cfg`` flag)

Use command ``apimetrics -a YOUR_API_KEY`` to save the key.

**Command-line usage**::

      usage: apimetrics [-h] [--apimetrics APIMETRICS] [--config CONFIG]
                        [--simulate]
                        {auth,call,deployment,report,token,workflow,alert,notification}
                        ...
      
      positional arguments:
        {auth,call,deployment,report,token,workflow,alert,notification}
                              sub-command help
          auth                auth help
          call                call help
          deployment          deployment help
          report              report help
          token               token help
          workflow            workflow help
          alert               alert help
          notification        notification help
      
      optional arguments:
        -h, --help            show this help message and exit
      
      apimetrics:
        APImetrics settings
      
        --apimetrics APIMETRICS, -a APIMETRICS
                              Set the APImetrics key to use
        --config CONFIG, -cfg CONFIG
                              Set the config file to use
        --simulate, -s        Simulate - don't call the APImetrics API


**APImetrics module**

You may also write your own scripts - look in the ``apimetrics/scripts`` folder for example code.

The example may also be called from the command line, e.g.:
 ``python -m apimetrics.scripts.delete_deployments --name "^z "``


This version tested with Python 2.7.6 and 3.5.2
