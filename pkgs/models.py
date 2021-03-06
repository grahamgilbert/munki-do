#from django.db import models
import os
import sys
import subprocess
import plistlib
import optparse
import fnmatch

from django.conf import settings
from django.db import models

#DEFAULT_MAKECATALOGS = "/usr/local/munki/makecatalogs"
DEFAULT_MAKECATALOGS = "/munki-tools/code/client/makecatalogs"
REPO_DIR = settings.MUNKI_REPO_DIR

def fail(message):
    sys.stderr.write(message)
    sys.exit(1)

def execute(command):    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        print(line) # yield line

usage = "%prog [options]"
o = optparse.OptionParser(usage=usage)

o.add_option("--makecatalogs", default=DEFAULT_MAKECATALOGS,
    help=("Path to makecatalogs. Defaults to '%s'. "
              % DEFAULT_MAKECATALOGS))

opts, args = o.parse_args()

MAKECATALOGS = opts.makecatalogs

# Read contents of all pkginfo files. You should be able to do this by reading the contents of catalogs/all

class Packages(object):
    @classmethod
    def detail(self, findtext):
        '''Returns a list of available pkgs, which is a list
        of pkg names (strings)'''
        all_catalog_path = os.path.join(REPO_DIR, 'catalogs/all')
        if os.path.exists(all_catalog_path):
            try:
                all_catalog_items = plistlib.readPlist(all_catalog_path)
                all_catalog_items = sorted(all_catalog_items, key=lambda x: (x['name'].lower(), x['version']))
                index = 0
                for item in all_catalog_items:
                    item['index'] = index
                    index += 1
                if findtext:
                    filtered_list = []
                    for item in all_catalog_items:
                        if fnmatch.fnmatch(item['name'].lower(), findtext.lower()):
                            filtered_list.append(item)
                    return filtered_list
                else:
                    return all_catalog_items
            except Exception, errmsg:
                return None
        else:
            return None

    @classmethod
    def move(self, pkg_name, pkg_version, pkg_catalog):
        '''Rewrites the catalog of the selected pkginfo files. Adapted from grahamgilbert/munki-trello'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                # Try, because it's conceivable there's a broken / non plist
                plist = None
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    plist['catalogs'] = [pkg_catalog]
                    plistlib.writePlist(plist, os.path.join(root, name))
                    done = True
                    break
            if done:
                break

    @classmethod
    def add(self, pkg_name, pkg_version, pkg_orig, pkg_catalog):
        '''Appends the catalog of the selected pkginfo files.'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                plist = None
                # Try, because it's conceivable there's a broken / non plist
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    # Check that the catalog is not already in this plist
                    if pkg_catalog not in plist['catalogs']:
                        plist['catalogs'].append(pkg_catalog)
                        plistlib.writePlist(plist, os.path.join(root, name))
                    done = True
                    break
            if done:
                break

    @classmethod
    def remove(self, pkg_name, pkg_version, pkg_orig):
        '''Removes the selected catalog from the pkginfo files.'''
        done = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                # Try, because it's conceivable there's a broken / non plist
                plist = None
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    current_catalogs = plist['catalogs']
                    # Try to remove this catalog from the array if it exists
                    try:
                        plist['catalogs'].remove(pkg_orig)
                    except:
                        pass
                    plistlib.writePlist(plist, os.path.join(root, name))
                    done = True
                    break
            if done:
                break

    @classmethod
    def delete_pkgs(self, pkg_name, pkg_version):
        '''Deletes a package and its associated pkginfo file, then induces makecatalogs'''
        done_delete = False
        for root, dirs, files in os.walk(os.path.join(REPO_DIR,'pkgsinfo'), topdown=False):
            for name in files:
                # Try, because it's conceivable there's a broken / non plist
                plist = None
                try:
                    plist = plistlib.readPlist(os.path.join(root, name))
                except:
                    pass
                if plist and plist['name'] == pkg_name and plist['version'] == pkg_version:
                    pkg_to_delete = plist['installer_item_location']
                    os.remove(os.path.join(root, name))
                    os.remove(os.path.join(REPO_DIR,'pkgs',pkg_to_delete))
                    done_delete = True
                    break
            if done_delete:
                break

    @classmethod
    def makecatalogs(self):
        task = execute([MAKECATALOGS, REPO_DIR])

class Pkgs(models.Model):
    class Meta:
        permissions = (("can_view_pkgs", "Can view packages"),)