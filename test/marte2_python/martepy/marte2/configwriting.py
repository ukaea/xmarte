# pylint: disable=C0103
"""A module for creating MARTe configuration files in the output"""

import warnings

class ConfigWriter:
    ''' The Configuration Writer base class that is used by all MARTe2 objects 
    to write their configuration representation. '''
    def __init__(self, tab_text='    '):
        self.sectionStack = []
        self.tab = 0
        self.tab_text = tab_text

    def _output(self, line):
        ''' Internally used to produce the line output '''
        raise NotImplementedError('Please use a child class of ConfigWriter')

    def setTab(self, newtab, override=False):
        ''' Set the tab indentation currently.'''
        if len(self.sectionStack) != 0:
            if override:
                msg = f"Setting tab, section stack isn't empty! Tab was {self.tab}, now {newtab}"
                warnings.warn(msg, UserWarning)
            else:
                msg = f'''Asked to setTab({newtab}) when stack isn't empty.
Tab = {self.tab}, Stack = {self.sectionStack[-1]}'''
                raise IndexError(msg)
        self.tab = newtab

    def startSection(self, name):
        ''' Start a new indentation section encapsulated with {} but not necessarily
        a new class - does not enforce the class definition line. '''
        self.writeBareLine(f'{name} = {{')
        self.tab += 1
        self.sectionStack.append(name)

    def writeNode(self, name, value):
        ''' Write parameter or basic line'''
        self.writeBareLine(f'{name} = {value}')

    def writeMARTe2Vector(self, name, data, formatAsFloat=True):
        ''' Write a MARTe2 vector/array. '''
        if formatAsFloat:
            datastring = ' '.join(['%g' % d for d in data]) # pylint: disable=C0209
        else:
            datastring = ' '.join([f'{d}' for d in data])
        self.writeNode(name, f'{{ {datastring} }}')

    def writeBareLine(self, line):
        ''' Write a basic line as given with the current set tab indentation '''
        prefix = self.getPrefix()
        self._output(f'{prefix}{line}')

    def startClass(self, name, typename):
        ''' Begin writing a class, encapsulating it with { and enforcing the Class
        definition is written. '''
        self.startSection(name)
        self.writeNode('Class', typename)

    def endSection(self, name):
        ''' End the current section - must be the current section and must match in starting
        name. '''
        if self.sectionStack[-1] == name:
            self.tab -= 1
            self.writeBareLine('}')
            self.sectionStack.pop()
        else:
            raise IndexError(f'Failed trying to close section "{name}"')

    def getPrefix(self):
        ''' Get the current tab index in number of spaces.'''
        if self.tab < 0:
            raise IndexError(f'Tab Error, tab is set to: {self.tab}')
        return ''.join([self.tab_text]*self.tab)

class StringConfigWriter(ConfigWriter):
    '''The derived class which actually outputs when used a string output and returns the
    MARTe2 object as a string object. '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lines = []
    def _output(self, line):
        ''' Append to our existing lines. '''
        self.lines.append(line)
    def __repr__(self):
        ''' Give a full output string format of the configuration object '''
        return '\n'.join(self.toLines())
    def toString(self):
        ''' Produce the object as a string '''
        return str(self)
    def toLines(self):
        ''' Return the currently defined lines. '''
        return self.lines
