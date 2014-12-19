# -*- coding: utf-8 -*-

#!/usr/bin/python

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



import argparse
import codecs
import glob
import os
import re
import sys
from itertools import dropwhile
from subprocess import PIPE, Popen


configs = {
    'backoffice': {
        'dir': 'backtoshops',
        'localedir': 'backtoshops/locale',
        'extensions': ['.html'],
    },
    'front': {
        'dir': 'front',
        'localedir': 'locale',
        'extensions': ['.html'],
    },
}


class CommandError(Exception):
    pass

def _popen(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE,
              close_fds=os.name != 'nt', universal_newlines=True)
    return p.communicate()

def _popen2(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE,
              close_fds=os.name != 'nt', universal_newlines=True)
    text, errors = p.communicate()
    if p.returncode == 0:
        if errors and not text:
            text = errors
    else:
        raise CommandError("errors happened while running '%s'\n%s"
                           % (cmd, errors))
    sys.stdout.write(text)
    return text

def find_files(domain):
    files = []
    if domain in configs:
        path_pattern = '%s/*' % configs[domain]['dir']
        extensions = configs[domain]['extensions']
        while glob.glob(path_pattern):
            for ext in ['.py'] + extensions:
                _all = glob.glob('%s%s' % (path_pattern, ext))
                files += filter(os.path.isfile, _all)
            path_pattern += '/*'
    files.sort()
    return files


def makemessages(domain, locale):
    if domain:
        domains = [domain]
    else:
        domains = configs.keys()

    for d in domains:
        if d in configs:
            sys.stdout.write("domain: %s\n" % d)

            locales = _get_locales(locale, configs[d]['localedir'])
            if d == 'backoffice':
                if locales:
                    for _locale in locales:
                        cmd = ";".join([
                                "cd %s" % configs[d]['dir'],
                                "./manage.py makemessages --locale=%s" % _locale])
                        _popen2(cmd)
                else:
                    cmd = ";".join([
                            "cd %s" % configs[d]['dir'],
                            "./manage.py makemessages"])
                    _popen2(cmd)
            else:
                for _locale in locales:
                    _makemessages(d, _locale,
                                  configs[d]['localedir'],
                                  configs[d]['extensions'])
        else:
            sys.stdout.write("invalid domain: %s\n" % d)

def _get_locales(locale, localedir):
    languages = []
    if locale is not None:
        languages.append(locale)
    else:
        locale_dirs = filter(os.path.isdir, glob.glob('%s/*' % localedir))
        languages = [os.path.basename(d) for d in locale_dirs]
    return languages

def _makemessages(domain, locale, localedir, extensions):
    sys.stdout.write("processing language %s\n" % locale)

    basedir = os.path.join(localedir, locale, 'LC_MESSAGES')
    if not os.path.isdir(basedir):
        os.makedirs(basedir)

    pofile = '%s/%s.po' % (basedir, domain)
    potfile = '%s/%s.pot' % (basedir, domain)
    if os.path.exists(potfile):
        os.unlink(potfile)

    for ff_name in find_files(domain):
        dirpath, f_name = os.path.split(ff_name)
        file_base, file_ext = os.path.splitext(f_name)

        if domain == 'front' \
                and (file_ext == '.py' or file_ext in extensions):
            thefile = f_name
            if file_ext in extensions:
                thefile = '%s.py' % f_name
                import tenjin
                src = tenjin.Template(ff_name).script
                with open(os.path.join(dirpath, thefile), "w") as f:
                    f.write(src)
        else:
            continue

        cmd = (
            'xgettext -d %s -L Python --keyword=gettext_noop '
            '--keyword=gettext_lazy --keyword=ngettext_lazy:1,2 '
            '--keyword=ugettext_noop --keyword=ugettext_lazy '
            '--keyword=ungettext_lazy:1,2 --keyword=pgettext:1c,2 '
            '--keyword=npgettext:1c,2,3 --keyword=pgettext_lazy:1c,2 '
            '--keyword=npgettext_lazy:1c,2,3 --from-code UTF-8 '
            '--add-comments=Translators -o - "%s"' % (
                domain, os.path.join(dirpath, thefile))
        )
        msgs, errors = _popen(cmd)
        if errors:
            if thefile != f_name:
                os.unlink(os.path.join(dirpath, thefile))
            if os.path.exists(potfile):
                os.unlink(potfile)
            raise CommandError(
                "errors happened while running xgettext on %s\n%s" %
                (f_name, errors))
        if msgs:
            if thefile != f_name:
                old = '#: ' + os.path.join(dirpath, thefile)
                new = '#: ' + ff_name
                msgs = msgs.replace(old, new)
            if os.path.exists(potfile):
                # Strip the header
                msgs = '\n'.join(dropwhile(len, msgs.split('\n')))
            else:
                msgs = msgs.replace('charset=CHARSET', 'charset=UTF-8')
            with open(potfile, 'ab') as f:
                f.write(msgs)
        if thefile != f_name:
            os.unlink(os.path.join(dirpath, thefile))


    if os.path.exists(potfile):
        msgs, errors = _popen('msguniq --to-code=utf-8 "%s"' % potfile)
        if errors:
            os.unlink(potfile)
            raise CommandError(
                "errors happened while running msguniq\n%s" % errors)

        if os.path.exists(pofile):
            with open(potfile, 'w') as f:
                f.write(msgs)
            msgs, errors = _popen('msgmerge -q "%s" "%s"' %
                                  (pofile, potfile))
            if errors:
                os.unlink(potfile)
                raise CommandError(
                    "errors happened while running msgmerge\n%s" % errors)

        with open(pofile, 'wb') as f:
            f.write(msgs)
        os.unlink(potfile)


def compilemessages(domain, locale):
    if domain:
        domains = [domain]
    else:
        domains = configs.keys()

    for d in domains:
        if d in configs:
            sys.stdout.write("domain: %s\n" % d)
            if d == 'backoffice':
                if locale:
                    cmd = ";".join([
                        "cd %s" % configs[d]['dir'],
                        "./manage.py compilemessages --locale=%s" % locale,
                    ])
                    _popen2(cmd)
                else:
                    cmd = ";".join([
                        "cd %s" % configs[d]['dir'],
                        "./manage.py compilemessages",
                    ])
                    _popen2(cmd)
            else:
                _compilemessages(d, locale,
                                 configs[d]['localedir'])
        else:
            sys.stdout.write("invalid domain: %s\n" % d)

def _compilemessages(domain, locale, localedir):
    basedirs = [localedir]
    basedirs = set(map(os.path.abspath, filter(os.path.isdir, basedirs)))
    for basedir in basedirs:
        if locale:
            basedir = os.path.join(basedir, locale, 'LC_MESSAGES')
        for dirpath, dirnames, filenames in os.walk(basedir):
            for f in filenames:
                if f.endswith('.po'):
                    sys.stdout.write('processing file %s in %s\n' % (f, dirpath))
                    fn = os.path.join(dirpath, f)
                    if has_bom(fn):
                        raise CommandError("The %s file has a BOM (Byte Order Mark). "
                            "only supports .po files encoded in UTF-8 and without any BOM." % fn)
                    pf = os.path.splitext(fn)[0]
                    # Store the names of the .mo and .po files in an environment
                    # variable, rather than doing a string replacement into the
                    # command, so that we can take advantage of shell quoting, to
                    # quote any malicious characters/escaping.
                    # See http://cyberelk.net/tim/articles/cmdline/ar01s02.html
                    os.environ['compilemo'] = pf + '.mo'
                    os.environ['compilepo'] = pf + '.po'
                    cmd = 'msgfmt --check-format -o "$compilemo" "$compilepo"'
                    os.system(cmd)

def has_bom(fn):
    f = open(fn, 'r')
    sample = f.read(4)
    return sample[:3] == '\xef\xbb\xbf' or \
            sample.startswith(codecs.BOM_UTF16_LE) or \
            sample.startswith(codecs.BOM_UTF16_BE)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='i18ntext')
    parser.add_argument('action', metavar='action',
                        choices=['make', 'compile'])
    parser.add_argument('-l', '--locale', action='store')
    parser.add_argument('-d', '--domain', action='store',
                        choices=['backoffice', 'front'])

    try:
        args = parser.parse_args()
        if args.action == 'make':
            makemessages(args.domain, args.locale)
        elif args.action == 'compile':
            compilemessages(args.domain, args.locale)
        else:
            parser.print_help()
            sys.exit(1)

    except CommandError, e:
        sys.stderr.write(str(e))
        sys.exit(1)

