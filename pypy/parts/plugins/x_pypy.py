import os.path

import snapcraft


class PyPyPlugin(snapcraft.BasePlugin):
    """A snapcraft plugin for building pypy.

    See:
      http://snapcraft.io/docs/build-snaps/plugins#adding-custom-plugins
      http://pypy.org/download.html#building-from-source
      http://pypy.readthedocs.io/en/latest/build.html#run-the-translation
    """

    MIN_MEMORY = 5 * 1024 * 1024  # kB, on 64-bit host

    @classmethod
    def schema(cls):
        schema = super().schema()
        schema['properties']['jit'] = {
            'type': 'boolean',
            'default': False,
        }
        #schema['properties']['sandbox'] = {
        #    'type': 'boolean',
        #    'default': False,
        #}
        #schema['properties']['build-timeout'] = {
        #    'type': 'number',
        #    'default': None,
        #}

        # Inform Snapcraft of the properties associated with building. If these
        # change in the YAML Snapcraft will consider the build step dirty.
        schema['build-properties'].extend(['jit'])

        return schema

    def build(self):
        super().build()
        self._check_memory()

        self.run(['pypy',
                  os.path.join(self.builddir, 'rpython/bin/rpython'),
                  '-Ojit' if self.options.jit else '-O2',
                  'targetpypystandalone',
                  ],
                 cwd=os.path.join(self.builddir, 'pypy/goal'),
                 )

        # packaging
        self.run(['python',
                  'package.py',
                  'pypy-release',  # the package name
                  ],
                 cwd=os.path.join(self.builddir, 'pypy/tool/release'),
                 )

    def _check_memory(self):
        available = _get_available_memory()
        if available is None:
            return
        if available < self.MIN_MEMORY:
            raise RuntimeError('need at least 5 GB memory, found {:.2} GB'
                               .format(available/(1024*1024)))


def _get_available_memory():
    """Return the total amount of available system memory, in kB."""
    with open('/proc/meminfo') as file:
        for line in file:
            if line.startswith('MemAvailable:'):
                raw = line.strip().rstrip(' kB').partition(':')[2].strip()
                return int(raw)
    return None
