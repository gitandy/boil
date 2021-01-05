import os
import sys
import glob
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
        return cls._run_proc('git', 'describe', '--tags')

    @classmethod
    def get_git_branch(cls, _):
        branch = cls._run_proc('git', 'rev-parse', '--abbrev-ref', 'HEAD')
        return branch if not branch == 'master' else ''

    @classmethod
    def get_git_modified(cls, _):
        return 'Modified' if len(cls._run_proc('git', 'diff', '--name-only')) > 0 else ''

    @staticmethod
    def do_write(args):
        if len(args) > 1:
            file = args[0]
            txt = ' '.join(args[1:])
        else:
            return False

        try:
            with open(file, 'wt') as f:
                f.write(txt+'\n')
            return True
        except OSError:
            return False

    @staticmethod
    def do_append(args):
        if len(args) > 1:
            file = args[0]
            txt = ' '.join(args[1:])
        else:
            return False

        try:
            with open(file, 'at') as f:
                f.write(txt+'\n')
                return True
        except OSError:
            return False

    @staticmethod
    def do_rm(file):
        try:
            for f in glob.iglob(file):
                os.remove(f)
            return True
        except FileNotFoundError:
            return True
        except (OSError, TypeError):
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
            res = subprocess.run([proc] if type(proc) is str else proc, capture_output=True)
            if res.returncode == 0:
                return str(res.stdout, sys.getdefaultencoding()).replace('\r', '').strip()
        except OSError as e:
            return None


class VarsDict(dict):
    def __missing__(self, key):
        return key


class Boiler:
    def __init__(self, recipe='Recipe', verbose=False):
        self._recipe_ = recipe
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

        self.read_recipe()

    def read_recipe(self):
        try:
            with open(self._recipe_, 'rt') as mf:
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

    def run_action(self, action, target):
        new_action = []
        for act in action:
            new_action.append(act.format_map({**self._vars_, **{'target': target}}))

        if self._verbose_:
            print(f'\tRunning {new_action}...')

        if action[0] == 'set':
            if len(new_action) == 3:
                self._vars_[new_action[1]] = new_action[2]
            elif len(new_action) > 3:
                self._vars_[new_action[1]] = ' '.join(new_action[2:])
            else:
                print(f'\tError running {new_action}: Too few arguments!')
        elif action[0] in ('do', 'get'):
            if len(new_action) > 1:
                args = []
                if len(new_action) > 2:
                    args = new_action[2:]

                if hasattr(InternalActions, new_action[0] + '_' + new_action[1]):
                    res = getattr(InternalActions, new_action[0] + '_' + new_action[1])(args)

                    if res is None or res is False:  # We don't want to fetch empty strings!
                        print(f'\tError running {new_action}: Internal command failed!')
                        sys.exit(1)
                    elif new_action[0] == 'get':
                        self._vars_[new_action[1]] = res
                else:
                    print(f'\tError running {new_action}: Internal command not available!')
                    sys.exit(1)
        else:
            try:
                res = subprocess.run(new_action, capture_output=True)
                if res.returncode != 0:
                    message = str(res.stderr, sys.getdefaultencoding().replace('\r', ''))
                    print(f'\tError running {action}: {message}')
                    sys.exit(1)
            except OSError as e:
                print(f'\tError running {action}: {e}')
                sys.exit(1)

    def boil(self, target='all'):
        if target not in self.targets:
            print(f'Error: Target \'{target}\' not available!')
        else:
            if not self.targets[target]['made']:
                for tgt in self.targets[target]['depends']:
                    if not self.targets[tgt]['made']:
                        self.boil(tgt)

                if target != '#default#':
                    print(f'Boiling target {target}...')

                for act in self.targets[target]['actions']:
                    self.run_action(act, target)

                if target != '#default#':
                    print('\t...done!')

                self.targets[target]['made'] = True


def print_help(path):
    f"""Usage: {path} [-f RECIPE] [TARGET]
       {path} -h"""


if __name__ == '__main__':
    boiler = None

    target = 'all'
    if len(sys.argv) > 1:
        target = sys.argv.pop(1)

    verbose = False
    if target == '-v':
        verbose = True
        target = 'all'
        if len(sys.argv) > 1:
            target = sys.argv.pop(1)

    recipe = 'Recipe'
    if target == '-f':
        if len(sys.argv) > 1:
            recipe = sys.argv.pop(1)
            target = 'all'
            boiler = Boiler(recipe, verbose)
        else:
            print_help(sys.argv[0])
            sys.exit(1)
    elif target == '-h':
        print_help(sys.argv[0])
        sys.exit(0)
    else:
        boiler = Boiler(verbose=verbose)

    if len(sys.argv) > 1:
        target = sys.argv.pop(1)

    boiler.boil(target)
