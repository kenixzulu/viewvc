# -*- Mode: python -*-
#
# Copyright (C) 2000-2002 The ViewCVS Group. All Rights Reserved.
#
# By using this file, you agree to the terms and conditions set forth in
# the LICENSE.html file which can be found at the top level of the ViewCVS
# distribution or at http://viewcvs.sourceforge.net/license-1.html.
#
# Contact information:
#   Greg Stein, PO Box 760, Palo Alto, CA, 94302
#   gstein@lyra.org, http://viewcvs.sourceforge.net/
#
# -----------------------------------------------------------------------
#
# Note: a t_start/t_end pair consumes about 0.00005 seconds on a P3/700.
#       the lambda form (when debugging is disabled) should be even faster.
#

import sys


SHOW_TIMES = 0
SHOW_CHILD_PROCESSES = 0

if SHOW_TIMES:

  import time

  _timers = { }
  _times = { }

  def t_start(which):
    _timers[which] = time.time()

  def t_end(which):
    t = time.time() - _timers[which]
    if _times.has_key(which):
      _times[which] = _times[which] + t
    else:
      _times[which] = t

  def dump():
    for name, value in _times.items():
      print '%s: %.6f<br>' % (name, value)

else:

  t_start = t_end = dump = lambda *args: None


class ViewCVSException:
  def __init__(self, msg, status=None):
    self.msg = msg
    self.status = status

  def __str__(self):
    if self.status:
      return '%s: %s' % (self.status, self.msg)
    return "ViewCVS Unrecoverable Error: %s" % self.msg

### backwards compat
ViewcvsException = ViewCVSException


def PrintStackTrace(server, text=''):
  import traceback, string

  server.write("<hr><p><font color=red>%s</font></p>\n<p><pre>" % text)
  server.write(server.escape(string.join(traceback.format_stack(), '')))
  server.write("</pre></p>")
  server.flush()


def PrintException(server, exc_data):
  status = exc_data['status']
  msg = exc_data['msg']
  tb = exc_data['stacktrace']
  
  server.header(status=status)
  server.write("<h3>An Exception Has Occurred</h3>\n")

  s = ''
  if msg:
    s = '<p><pre>%s</pre></p>' % server.escape(msg)
  if status:
    s = s + ('<h4>HTTP Response Status</h4>\n<p><pre>\n%s</pre></p><hr>\n'
             % status)
  server.write(s)

  server.write("<h4>Python Traceback</h4>\n<p><pre>")
  server.write(server.escape(tb))
  server.write("</pre></p>\n")


def GetExceptionData():
  # capture the exception before doing anything else
  exc_type, exc, exc_tb = sys.exc_info()

  exc_dict = {
    'status' : None,
    'msg' : None,
    'stacktrace' : None,
    }
  
  try:
    import traceback, string

    if isinstance(exc, ViewCVSException):
      exc_dict['msg'] = exc.msg
      exc_dict['status'] = exc.status
    
    tb = string.join(traceback.format_exception(exc_type, exc, exc_tb), '')
    exc_dict['stacktrace'] = tb

  finally:
    # prevent circular reference. sys.exc_info documentation warns
    # "Assigning the traceback return value to a local variable in a function
    # that is handling an exception will cause a circular reference..."
    # This is all based on 'exc_tb', and we're now done with it. Toss it.
    del exc_tb

  return exc_dict


if SHOW_CHILD_PROCESSES:
  class Process:
    def __init__(self, command, inStream, outStream, errStream):
      self.command = command
      self.debugIn = inStream
      self.debugOut = outStream
      self.debugErr = errStream

      import sapi
      if not sapi.server is None:
        if not sapi.server.pageGlobals.has_key('processes'):
          sapi.server.pageGlobals['processes'] = [self]
        else:
          sapi.server.pageGlobals['processes'].append(self)

  def DumpChildren(server):
    import os

    if not server.pageGlobals.has_key('processes'):
      return
    
    server.header()
    lastOut = None
    i = 0

    for k in server.pageGlobals['processes']:
      i = i + 1
      server.write("<table border=1>\n")
      server.write("<tr><td colspan=2>Child Process%i</td></tr>" % i)
      server.write("<tr>\n  <td valign=top>Command Line</td>  <td><pre>")
      server.write(server.escape(k.command))
      server.write("</pre></td>\n</tr>\n")
      server.write("<tr>\n  <td valign=top>Standard In:</td>  <td>")

      if k.debugIn is lastOut and not lastOut is None:
        server.write("<i>Output from process %i</i>" % (i - 1))
      elif k.debugIn:
        server.write("<pre>")
        server.write(server.escape(k.debugIn.getvalue()))
        server.write("</pre>")
        
      server.write("</td>\n</tr>\n")
      
      if k.debugOut is k.debugErr:
        server.write("<tr>\n  <td valign=top>Standard Out & Error:</td>  <td><pre>")
        if k.debugOut:
          server.write(server.escape(k.debugOut.getvalue()))
        server.write("</pre></td>\n</tr>\n")
        
      else:
        server.write("<tr>\n  <td valign=top>Standard Out:</td>  <td><pre>")
        if k.debugOut:
          server.write(server.escape(k.debugOut.getvalue()))
        server.write("</pre></td>\n</tr>\n")
        server.write("<tr>\n  <td valign=top>Standard Error:</td>  <td><pre>")
        if k.debugErr:
          server.write(server.escape(k.debugErr.getvalue()))
        server.write("</pre></td>\n</tr>\n")

      server.write("</table>\n")
      server.flush()
      lastOut = k.debugOut

    server.write("<table border=1>\n")
    server.write("<tr><td colspan=2>Environment Variables</td></tr>")
    for k, v in os.environ.items():
      server.write("<tr>\n  <td valign=top><pre>")
      server.write(server.escape(k))
      server.write("</pre></td>\n  <td valign=top><pre>")
      server.write(server.escape(v))
      server.write("</pre></td>\n</tr>")
    server.write("</table>")
         
else:

  def DumpChildren(server):
    pass
    
