# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################



# The default ``config.py``


def set_prefs(prefs):
    """This function is called before opening the project"""

    # Specify which files and folders to ignore in the project.
    # Changes to ignored resources are not added to the history and
    # VCSs.  Also they are not returned in `Project.get_files()`.
    # Note that ``?`` and ``*`` match all characters but slashes.
    # '*.pyc': matches 'test.pyc' and 'pkg/test.pyc'
    # 'mod*.pyc': matches 'test/mod1.pyc' but not 'mod/1.pyc'
    # '.svn': matches 'pkg/.svn' and all of its children
    # 'build/*.o': matches 'build/lib.o' but not 'build/sub/lib.o'
    # 'build//*.o': matches 'build/lib.o' and 'build/sub/lib.o'
    prefs['ignored_resources'] = ['*.pyc', '*~', '.ropeproject',
                                  '.hg', '.svn', '_svn', '.git']

    # Specifies which files should be considered python files.  It is
    # useful when you have scripts inside your project.  Only files
    # ending with ``.py`` are considered to be python files by
    # default.
    #prefs['python_files'] = ['*.py']

    # Custom source folders:  By default rope searches the project
    # for finding source folders (folders that should be searched
    # for finding modules).  You can add paths to that list.  Note
    # that rope guesses project source folders correctly most of the
    # time; use this if you have any problems.
    # The folders should be relative to project root and use '/' for
    # separating folders regardless of the platform rope is running on.
    # 'src/my_source_folder' for instance.
    #prefs.add('source_folders', 'src')

    # You can extend python path for looking up modules
    #prefs.add('python_path', '~/python/')

    # Should rope save object information or not.
    prefs['save_objectdb'] = True
    prefs['compress_objectdb'] = False

    # If `True`, rope analyzes each module when it is being saved.
    prefs['automatic_soa'] = True
    # The depth of calls to follow in static object analysis
    prefs['soa_followed_calls'] = 0

    # If `False` when running modules or unit tests "dynamic object
    # analysis" is turned off.  This makes them much faster.
    prefs['perform_doa'] = True

    # Rope can check the validity of its object DB when running.
    prefs['validate_objectdb'] = True

    # How many undos to hold?
    prefs['max_history_items'] = 32

    # Shows whether to save history across sessions.
    prefs['save_history'] = True
    prefs['compress_history'] = False

    # Set the number spaces used for indenting.  According to
    # :PEP:`8`, it is best to use 4 spaces.  Since most of rope's
    # unit-tests use 4 spaces it is more reliable, too.
    prefs['indent_size'] = 4

    # Builtin and c-extension modules that are allowed to be imported
    # and inspected by rope.
    prefs['extension_modules'] = []

    # Add all standard c-extensions to extension_modules list.
    prefs['import_dynload_stdmods'] = True

    # If `True` modules with syntax errors are considered to be empty.
    # The default value is `False`; When `False` syntax errors raise
    # `rope.base.exceptions.ModuleSyntaxError` exception.
    prefs['ignore_syntax_errors'] = False

    # If `True`, rope ignores unresolvable imports.  Otherwise, they
    # appear in the importing namespace.
    prefs['ignore_bad_imports'] = False

    prefs.add('python_path', '/Users/guillaume/.virtualenvs/backtoshops/lib/python2.7/site-packages/')
    prefs.add('python_path', '/Users/guillaume/Projects/BTS/backtoshops/')

def project_opened(project):
    """This function is called after opening the project"""
    # Do whatever you like here!

