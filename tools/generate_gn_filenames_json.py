#!/usr/bin/env python
import json
import os
import sys

import install


def LoadPythonDictionary(path):
  file_string = open(path).read()
  try:
    file_data = eval(file_string, {'__builtins__': None}, None)
  except SyntaxError, e:
    e.filename = path
    raise
  except Exception, e:
    raise Exception("Unexpected error while reading %s: %s" % (path, str(e)))

  assert isinstance(file_data, dict), "%s does not eval to a dictionary" % path

  return file_data


FILENAMES_JSON_HEADER = '''
// This file is automatically generated by generate_gn_filenames_json.py
// DO NOT EDIT
'''.lstrip()


if __name__ == '__main__':
  node_root_dir = os.path.dirname(os.path.dirname(__file__))
  node_gyp_path = os.path.join(node_root_dir, 'node.gyp')
  out = {}
  node_gyp = LoadPythonDictionary(node_gyp_path)
  out['library_files'] = node_gyp['variables']['library_files']
  node_lib_target = next(
      t for t in node_gyp['targets']
      if t['target_name'] == '<(node_lib_target_name)')
  node_source_blacklist = {
      '<@(library_files)',
      'common.gypi',
      '<(SHARED_INTERMEDIATE_DIR)/node_javascript.cc',
  }
  out['node_sources'] = [
      f for f in node_lib_target['sources']
      if f not in node_source_blacklist]

  out['headers'] = []

  def add_headers(files, dest_dir):
    if 'src/node.h' in files:
      files = [f for f in files if f.endswith('.h') and f != 'src/node_version.h']
    elif any(f.startswith('deps/v8/') for f in files):
      files = [f.replace('deps/v8/', '//v8/', 1) for f in files]
    hs = {'files': sorted(files), 'dest_dir': dest_dir}
    out['headers'].append(hs)

  install.variables = {'node_shared_libuv': 'false'}
  install.headers(add_headers)
  with open(os.path.join(node_root_dir, 'filenames.json'), 'w') as f:
    f.write(FILENAMES_JSON_HEADER)
    f.write(json.dumps(out, sort_keys=True, indent=2, separators=(',', ': ')))
    f.write('\n')
