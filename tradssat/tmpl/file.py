import os
import re

import numpy as np
from tradssat.utils import detect_encod

from .vals import FileValueSet, ValueSubSection
from .var import VariableSet, CODE_MISS


class File(object):
    def __init__(self, file):
        """

        Parameters
        ----------
        file: str

        """
        self.file = file
        self._var_info = VariableSet(self._get_var_info())

        self._values = FileValueSet()
        self.encoding = detect_encod(self.file)
        self._read()

    def _read(self):

        with open(self.file, encoding=self.encoding) as f:
            section = []  # To store lines that go in the same section
            for l in f.readlines():

                if l[0] == '!':  # skip comments
                    continue

                if l[0] == '*':  # start of section

                    # Process any previously stored block
                    if len(section):
                        self._read_section(section)

                    # Clear the current block
                    section.clear()

                if len(l.strip()):
                    section.append(l)  # Append current line to block

            # Read the last block too
            self._read_section(section)

    def get_var_type(self, var, sect=None):
        return self.get_var(var, sect).type_

    def get_var_spc(self, var, sect=None):
        return self.get_var(var, sect).spc

    def get_var_size(self, var, sect=None):
        return self.get_var(var, sect).size

    def get_var_miss(self, var, sect=None):
        return self.get_var(var, sect).miss

    def get_var(self, var, sect=None):
        return self._var_info.get_var(var, sect)

    def get_val(self, var, sect=None):
        return self._values[var]['val']

    def get_dims_val(self, var):
        return self.get_val(var).shape

    def to_dict(self):
        return self._values.to_dict()

    def _read_subsection(self, section_name, subblock):

        var_names = self._get_var_names(subblock[0])

        n_lines = len(subblock) - 1  # -1 for the header line (with "@" )
        lengths = [self.get_var_size(vr) for vr in var_names]
        spaces = [self.get_var_spc(vr) for vr in var_names]
        cum_lens = np.insert(np.cumsum(lengths) + np.cumsum(spaces), 0, 0)
        cutoffs = [(cum_lens[i], cum_lens[i + 1] + 1) for i in range(len(var_names))]

        d_vals = {vr: self._gen_empty_mtrx(vr, n_lines) for vr in var_names}

        for i, l in enumerate(subblock[1:]):
            vals = [l[c[0]:c[1]].strip() for c in cutoffs]
            for vr, vl in zip(var_names, vals):
                if not len(vl) or vl == self.get_var_miss(vr):
                    vl = CODE_MISS
                d_vals[vr][i] = vl

        subsect = ValueSubSection()
        for vr in var_names:
            subsect.set_value(vr, d_vals[vr])

        self._values[section_name].add_subsection(subsect)

    def _read_section(self, section):
        section_name, section_lines = self._process_section_header(section)

        subblock = []
        for l in section_lines:  # skip first line (with "*")
            if l[0] == '@':

                if len(subblock):
                    self._read_subsection(section_name, subblock)
                subblock.clear()

            # Append current line to section
            if len(l.strip()):
                subblock.append(l)

        if len(subblock):
            self._read_subsection(section_name, subblock)

    def _gen_empty_mtrx(self, var, size):
        tp = self.get_var_type(var)
        if tp == 'float':
            dtype = float
        elif tp == 'int':
            dtype = int
        elif tp == 'str' or tp == str:
            str_size = self.get_var_size(var)
            dtype = f'U{str_size}'
        else:
            dtype = tp

        return np.full(size, CODE_MISS, dtype=dtype)

    def _get_var_names(self, line):
        names = [x.strip() for x in re.split('[. +]', line[1:]) if len(x.strip())]  # skip initial "@"
        final_names = []
        to_skip = []
        for i, vr in enumerate(names):
            if vr in to_skip:
                continue
            if vr in self._var_info:
                final_names.append(vr)
            elif i != len(names) - 1 and '{} {}'.format(vr, names[i + 1]) in self._var_info:
                final_names.append('{} {}'.format(vr, names[i + 1]))
                to_skip.append(names[i + 1])
            else:
                raise ValueError(
                    'Variable "{vr}" is not defined for file {nm}.'.format(vr=vr, nm=os.path.split(self.file)[1])
                )
        return final_names

    def _get_var_info(self):
        """
        Return a dictionary of variable information.

        Returns
        -------
        set[Variable]
        """

        raise NotImplementedError

    @classmethod
    def matches_file(cls, file):
        """

        Parameters
        ----------
        file: str

        Returns
        -------
        bool
        """
        raise NotImplementedError

    def _process_section_header(self, lines):
        """

        Parameters
        ----------
        lines

        Returns
        -------
        tuple[str, list]
        """

        raise NotImplementedError
