#!/usr/bin/env python
#
# Usage: ./ncf_rudder.py path
#
# This is a Python module containing functions to generate technique for Rudder from ncf techniques
#
# This module is designed to run on the latest major versions of the most popular
# server OSes (Debian, Red Hat/CentOS, Ubuntu, SLES, ...)
# At the time of writing (November 2013) these are Debian 7, Red Hat/CentOS 6,
# Ubuntu 12.04 LTS, SLES 11, ...
# The version of Python in all of these is >= 2.6, which is therefore what this
# module must support

import os.path
import ncf 
import sys

def write_all_techniques_for_rudder(root_path):
  write_category_xml(root_path)
  techniques = ncf.get_all_techniques_metadata()
  for technique, metadata in techniques.iteritems():
    try:
      write_technique_for_rudder(root_path, metadata)
    except Exception, e:
     print("Error: Unable to create Rudder Technique files related to NCF Technique "+technique+", skipping...")
     continue

def get_category_xml():
  """Create a category.xml content to be inserted in the NCF root directory"""

  content = []
  content.append('<xml>')
  content.append('  <name>Meta Techniques</name>')
  content.append('  <description>')
  content.append('    Meta Techniques created using the NCF framework.')
  content.append('  </description>')
  content.append('</xml>')

  # Join all lines with \n to get a pretty xml
  result = '\n'.join(content)+"\n"
  return result

def write_category_xml(path):
  """Write the category.xml file to make Rudder acknowledge this directory as a Technique section"""

  if not os.path.exists(path):
    os.makedirs(path)

  file = open(os.path.realpath(os.path.join(path, "category.xml")),"w")
  file.write(get_category_xml())
  file.close()

def write_technique_for_rudder(root_path, technique):
  """ From a technique, generate all files needed for Rudder in specified path"""

  path = get_path_for_technique(root_path,technique)
  if not os.path.exists(path):
    os.makedirs(path)
  write_xml_metadata_file(path,technique)
  write_expected_reports_file(path,technique)

def write_xml_metadata_file(path,technique):
  """ write metadata.xml file from a technique, to a path """
  file = open(os.path.realpath(os.path.join(path, "metadata.xml")),"w")
  content = get_technique_metadata_xml(technique)
  file.write(content)
  file.close()

def write_expected_reports_file(path,technique):
  """ write expected_reports.csv file from a technique, to a path """
  file = open(os.path.realpath(os.path.join(path, "expected_reports.csv")),"w")
  content = get_technique_expected_reports(technique)
  file.write(content)
  file.close()

def get_technique_metadata_xml(technique_metadata):
  """Get metadata xml for a technique as string"""

  # Get all generic methods
  generic_methods = ncf.get_all_generic_methods_metadata()

  content = []
  content.append('<TECHNIQUE name="'+technique_metadata['bundle_name']+'">')
  content.append('  <DESCRIPTION>'+technique_metadata['description']+'</DESCRIPTION>')
  content.append('  <BUNDLES>')
  content.append('    <NAME>'+ technique_metadata['bundle_name'] + '</NAME>')
  content.append('  </BUNDLES>')
  content.append('  <SECTIONS>')

  method_calls = technique_metadata["method_calls"]  

  # Get all method call, with no duplicate values
  methods_name = set()
  for method_call in method_calls:
    method_name = methods_name.add(method_call['method_name'])

  # For each method used, create a section containing all calls to that method
  section_list = []
  for method_name in methods_name:

    try:
      generic_method = generic_methods[method_name]
    except Exception, e:
      print "Error: The method '" + method_name + "' does not exist. Aborting Technique creation..."

    # Filter all method calls to get only those about that method
    filter_method_calls = [x for x in method_calls if x["method_name"] == method_name]
    # Generare xml for that section
    section = generate_section_xml(filter_method_calls, generic_method)
    section_list.extend(section)

  content.extend(section_list)
  content.append('  </SECTIONS>')
  content.append('</TECHNIQUE>')

  # Join all lines with \n to get a pretty xml
  result =  '\n'.join(content)+"\n"

  return result

def generate_section_xml(method_calls, generic_method):
  """ Generate xml section about a method used by that technique"""
  content = []
  content.append('    <SECTION component="true" multivalued="true" name="'+generic_method["name"]+'">')
  content.append('      <REPORTKEYS>')

  # For each method call, generate a value
  values = []
  for method_call in method_calls:
    # Generate XML for that method call
    value = generate_value_xml(method_call,generic_method)
    values.append(value)

  content.extend(values)
  content.append('      </REPORTKEYS>') 
  content.append('    </SECTION>')
  
  
  return content 
 
def generate_value_xml(method_call,generic_method):
  """Generate xml containing value needed for reporting from a method call"""
  try:
    parameter = method_call["args"][generic_method["class_parameter_id"]-1]
    value = generic_method["class_prefix"] + "_" + parameter
    
    return "        <VALUE>"+value+"</VALUE>"
  except:
    raise Exception("Method parameter \"" + generic_method['class_parameter_id'] + "\" is not defined")


def get_technique_expected_reports(technique_metadata):
  """Generates technique expected reports from technique metadata"""
  # Get all generic methods
  generic_methods = ncf.get_all_generic_methods_metadata()

  # Content start with a header
  content = ["""# This file contains one line per report expected by Rudder from this technique
# Format: technique_name;;class_prefix_${key};;@@RUDDER_ID@@;;component name;;component key"""]
  
  technique_name = technique_metadata['bundle_name']
  for method_call in technique_metadata["method_calls"]:
    method_name = method_call['method_name']
    generic_method = generic_methods[method_name]

    component = generic_method['name']
    key_value = method_call["args"][generic_method["class_parameter_id"]-1]
    class_prefix = generic_method["class_prefix"]+"_"+key_value

    line = technique_name+";;"+class_prefix+";;@@RUDDER_ID@@;;"+component+";;"+key_value
    
    content.append(line)

  # Join all lines + last line
  result = "\n".join(content)+"\n"
  return result


def get_path_for_technique(root_path, technique_metadata):
  """ Generate path where file about a technique needs to be created"""
  return os.path.join(root_path, technique_metadata['bundle_name'], technique_metadata['version'])

def usage():
  print("Usage: python ncf_rudder.py path")

if __name__ == '__main__':
  if len(sys.argv) == 2:
    write_all_techniques_for_rudder(sys.argv[1])
  else:
    usage()