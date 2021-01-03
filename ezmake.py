import os
import sys
import subprocess


__author__ = 'Andreas Schawo <andreas@schawo.de>, (c) 2021'
__license__ = 'This work is licensed under CC BY 4.0 https://creativecommons.org/licenses/by/4.0/'
__version__ = 'v0.1'


class InternalActions:
    # @staticmethod
    # def do_zip(name, *files):
    #     pass

    @staticmethod
    def do_print(text):
        if type(text) == list:
            print(' '.join(text))
        else:
            print(text)
        return True

    @classmethod
    def get_git_tag(cls, _):
        return cls._run_proc(['git', 'describe', '--tags'])

    @staticmethod
    def do_rm(file):
        try:
            os.remove(file[0])
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False

    @staticmethod
    def do_cd(path):
        try:
            os.chdir(path[0])
            return True
        except OSError:
            return False

    @staticmethod
    def do_mkdir(path):
        try:
            os.makedirs(path[0])
            return True
        except OSError:
            return False

    @staticmethod
    def do_rmdir(path):
        try:
            os.rmdir(path[0])
            return True
        except FileNotFoundError:
            return True
        except OSError:
            return False

    @staticmethod
    def _run_proc(*proc):
        """Runs a process with arguments
        :return Tuple of return code, stdout text, stderr text"""
        try:
            res = subprocess.run(list(proc) if type(proc) is str else proc, capture_output=True)
            if res.returncode == 0:
                return str(res.stdout, sys.getdefaultencoding()).replace('\r', '')
        except OSError as e:
            return None


class VarsDict(dict):
    def __missing__(self, key):
        return key


class EzMake:
    def __init__(self, makefile='ezMakefile', verbose=False):
        self._makefile_ = makefile
        self._verbose_ = verbose

        self.targets = {
            '#default#': {
                'depends': [],
                'actions': [],
                'made': False
            },
            'all': {
                'depends': ['#default#'],
                'actions': [],
                'made': False
            }}

        self._vars_ = VarsDict()

        self.read_makefile()

    def read_makefile(self):
        try:
            with open(self._makefile_, 'rt') as mf:
                target = '#default#'

                l_nr = 1
                for ln in mf.readlines():
                    if len(ln.strip()) == 0 or ln.strip().startswith('#'):
                        continue
                    elif ln.strip().startswith('>'):
                        tgt = ln.strip()[1:].split('>')
                        if len(tgt) > 0:
                            target = tgt[0].strip()

                        self.targets[target] = {
                            'depends': ['#default#'],
                            'actions': [],
                            'made': False
                        }

                        if len(tgt) > 1:
                            self.targets[target]['depends'] = tgt[1].strip().split(' ')

                        if self._verbose_:
                            print(f'Found target {target} on line {l_nr} depending on {self.targets[target]["depends"][1:]}')
                    elif ln.startswith('\t') or ln.startswith(' ') or target == '#default#':
                        self.targets[target]['actions'].append(ln.strip().split(' '))
                    else:
                        print(f'Error: Wrong format on line {l_nr}!')

                    l_nr += 1
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)

    def run_action(self, action):
        if action[0] in ('do', 'get'):
            if self._verbose_:
                print(f'\tRunning {action}...')

            if len(action) > 1:
                args = []
                if len(action) > 2:
                    args = action[2:]

                if hasattr(InternalActions, action[0] + '_' + action[1]):
                    res = getattr(InternalActions, action[0] + '_' + action[1])(args)

                    if not res:
                        print(f'\tError running {action}: Internal command failed!')
                        sys.exit(1)
                    elif action[0] == 'get':
                        self._vars_[action[1]] = res
                else:
                    print(f'\tError running {action}: Internal command not available!')
                    sys.exit(1)
        else:
            new_action = []
            for act in action:
                new_action.append(act.format_map(self._vars_))

            if self._verbose_:
                print(f'\tRunning {new_action}...')

            try:
                res = subprocess.run(new_action, capture_output=True)
                if res.returncode != 0:
                    message = str(res.stderr, sys.getdefaultencoding().replace('\r', ''))
                    print(f'\tError running {action}: {message}')
                    sys.exit(1)
            except OSError as e:
                print(f'\tError running {action}: {e}')
                sys.exit(1)

    def make(self, target='all'):
        if target not in self.targets:
            print(f'Error: Target \'{target}\' not available!')
        else:
            if not self.targets[target]['made']:
                for tgt in self.targets[target]['depends']:
                    if not self.targets[tgt]['made']:
                        self.make(tgt)

                if target != '#default#':
                    print(f'Making target {target}...')

                for act in self.targets[target]['actions']:
                    self.run_action(act)

                if target != '#default#':
                    print('\t...done!')

                self.targets[target]['made'] = True


def print_help(path):
    f"""Usage: {path} [-f MAKEFILE] [TARGET]
       {path} -h"""


if __name__ == '__main__':
    ez = None

    target = 'all'
    if len(sys.argv) > 1:
        target = sys.argv.pop(1)

    verbose = False
    if target == '-v':
        verbose = True
        target = 'all'
        if len(sys.argv) > 1:
            target = sys.argv.pop(1)

    makefile = 'ezMakefile'
    if target == '-f':
        if len(sys.argv) > 1:
            makefile = sys.argv.pop(1)
            target = 'all'
            ez = EzMake(makefile, verbose)
        else:
            print_help(sys.argv[0])
            sys.exit(1)
    elif target == '-h':
        print_help(sys.argv[0])
        sys.exit(0)
    else:
        ez = EzMake(verbose=verbose)

    if len(sys.argv) > 1:
        target = sys.argv.pop(1)

    ez.make(target)
