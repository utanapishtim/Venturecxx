# Copyright (c) 2016 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

"""Adapter for using Plex-like scanner libraries for writing VentureScript sublanguages.

The standard VentureScript sublanguage interface (see
:py:meth:`venture.ripl.ripl.Ripl.register_language`) expects the
VentureScript parser to control the input stream, and expects the
sublanguage parser to manifest as a procedure that accepts characters
and reports whether the utterance is complete and what it parsed to.

Many parser and scanner libraries, however, expect to themselves
control the input stream, i.e. provide a method like ``read(stream) -> result``.
Notably, this includes Plex, the library in which the VentureScript
scanner itself is written.

This module provides an adapter which uses multithreading (!) to
convert between the two interfaces, so a Plex-like scanner can be used
to implement a VentureScript sublanguage.
"""

import Queue
import threading

_HUNGRY_TOKEN = ['hungry']
_DEAD_CHAR = ['dead']

class _Dead(Exception):
  pass

class Reader(object):
  def __init__(self, char_queue, token_queue):
    self._char_queue = char_queue
    self._token_queue = token_queue

  def read(self, _n):
    self._token_queue.put(_HUNGRY_TOKEN)
    char = self._char_queue.get()
    if char is _DEAD_CHAR:
      raise _Dead
    return char

def _scan_thread(scan, char_queue, token_queue):
  try:
    reader = Reader(char_queue, token_queue)
    scanner = scan(reader)
    token, _text = scanner.read()
    token_queue.put(token)
  except _Dead:
    pass

class Scanner(object):
  def __init__(self, scanner):
    char_queue = Queue.Queue()
    token_queue = Queue.Queue()
    self._thread = threading.Thread(
      target=_scan_thread, args=(scanner, char_queue, token_queue))
    self._char_queue = char_queue
    self._token_queue = token_queue

    self._thread.start()
    token = self._token_queue.get()
    assert token is _HUNGRY_TOKEN

  def __del__(self):
    if self._thread is not None:
      self._char_queue.put(_DEAD_CHAR)
      self._thread.join()
      self._thread = None

  def __call__(self, text):
    self._char_queue.put(text)
    token = self._token_queue.get()
    if token is _HUNGRY_TOKEN:
      return False, None
    else:
      self._thread.join()
      self._thread = None
      return True, token
