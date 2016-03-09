from collections.abc import Mapping
import configparser
import os

class ImmutableMapping(Mapping):
  def __init__(self,_dict):
    self._dict=_dict
  def __getitem__(self,key):
    return self._dict[key]
  def __len__(self):
    return len(self._dict)
  def __iter__(self):
    yield from self._dict
  def __contains__(self,key):
    return key in self._dict
  def get(self, key, default=None):
    return self._dict.get(key,default)
  def __str__(self):
    return str(self._dict)
  def __repr__(self):
    return "<Immutable {}>".format(self._dict)

class SettingsSection(ImmutableMapping):
  def __init__(self,sections,values):
    super(SettingsSection,self).__init__(values)
    self.__sections=ImmutableMapping(sections)
  
  @property
  def sections(self):
    """Get the sections dictionary"""
    return self.__sections
  
  def __getattr__(self,name):
    if name[0]!="_":
      try:
        return self.__sections[name]
      except KeyError:
        pass
    raise AttributeError("'SettingsSection' object has no attribute '{}'".format(name))
  
  def __eq__(self,other):
    return super(SettingsSection,self).__eq__(other) and self.sections == other.sections
  
  def __str__(self):
    return "<Settings {}, subsections: {}>".format(self._dict,", ".join(self.__sections.keys()))
  def __repr__(self):
    return "<Settings {}, subsections: {}>".format(self._dict,self.__sections)

def _mergesettings(parent,sectiondict,section,value):
  for key in parent:
    if key not in value:
      value[key]=parent[key]
  for key in parent.sections:
    if key in sectiondict:
      _mergesettings(parent.sections[key],*sectiondict[key])
    else:
      section[key]=parent.sections[key]

def _loadsettings(filename,parent=None):
  sectiondicts={}
  sections={}
  values={}
  config = configparser.ConfigParser(interpolation=None,empty_lines_in_values=False,default_section="~#'&INVALID&'#~",dict_type=dict)
  
  try:
    config.read_file(open(filename,'r'))
  except FileNotFoundError as ex:
    if parent is None:
      raise ex
    else:
      return parent
  except configparser.Error as ex:
    print("Error reading config file")
    print(ex)
    if parent is None:
      raise ex
    else:
      return parent
  for sectionname in config.sections():
    sectiondict=sectiondicts
    section=sections
    value=values
    for el in sectionname.split("."):
      if el not in sectiondict:
        newsections={}
        newvalues={}
        sectiondict[el]=({},newsections,newvalues)
        section[el]=SettingsSection(newsections,newvalues)
      sectiondict,section,value=sectiondict[el]
    for key in config[sectionname]:
      value[key]=config[sectionname][key]
 
  if parent is not None: 
    _mergesettings(parent,sectiondicts,sections,values)

  return SettingsSection(sections,values)

def __print(section,indent=""):
  for key,value in section.items():
    print(indent,key,"=",value)
  for key,subsection in section.sections.items():
    print(indent,key,": {")
    __print(subsection,indent+"  ")
    print(indent,"}")

class Settings(object):
  def __new__(cls):
    try:
      return cls._instance
    except AttributeError:
      cls._instance = super(Settings,cls).__new__(cls)
      return cls._instance
  @property
  def system(self):
    """ System settings """
    try:
      return self._system
    except AttributeError:
      settingspath="/etc/alphagsm.conf" if __file__[:5]=="/usr/" else os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),"alphagsm.conf")
      self._system=_loadsettings(settingspath)
      return self._system
  @property
  def user(self):
    """ User settings """
    try:
      return self._user
    except AttributeError:
      settingspath=os.path.join(os.path.expanduser(self.system.sections.get('core',{}).get('userconf',"~/.alphagsm/")),"alphagsm.conf")
      self._user=_loadsettings(settingspath,self.system)
      return self._user

settings=Settings()