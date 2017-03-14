#!/usr/bin/env python
# Copyright (C) 2004,2005,2006,2008,2009,2010 Fabien SEISEN
# 
# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
# 
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
# ("PSF"), and the Individual or Organization ("Licensee") accessing and
# otherwise using this software ("Python") in source or binary form and
# its associated documentation.
# 
# 2. Subject to the terms and conditions of this License Agreement, PSF
# hereby grants Licensee a nonexclusive, royalty-free, world-wide
# license to reproduce, analyze, test, perform and/or display publicly,
# prepare derivative works, distribute, and otherwise use Python
# alone or in any derivative version, provided, however, that PSF's
# License Agreement and PSF's notice of copyright, i.e., "Copyright (c)
# 2001, 2002, 2003, 2004, 2005, 2006 Python Software Foundation; All Rights
# Reserved" are retained in Python alone or in any derivative version 
# prepared by Licensee.
# 
# 3. In the event Licensee prepares a derivative work that is based on
# or incorporates Python or any part thereof, and wants to make
# the derivative work available to others as provided herein, then
# Licensee hereby agrees to include in any such work a brief summary of
# the changes made to Python.
# 
# 4. PSF is making Python available to Licensee on an "AS IS"
# basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
# IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
# DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
# FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
# INFRINGE ANY THIRD PARTY RIGHTS.
# 
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
# FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
# A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
# OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
# 
# 6. This License Agreement will automatically terminate upon a material
# breach of its terms and conditions.
# 
# 7. Nothing in this License Agreement shall be deemed to create any
# relationship of agency, partnership, or joint venture between PSF and
# Licensee.  This License Agreement does not grant permission to use PSF
# trademarks or trade name in a trademark sense to endorse or promote
# products or services of Licensee, or any third party.
# 
# 8. By copying, installing or otherwise using Python, Licensee
# agrees to be bound by the terms and conditions of this License
# Agreement.
# 
"""
extend urllib2 to enable uploading files using multipart/form-data

I was looking for something to make me able to upload files to my photo web site (http://gallery.menalto.com/).
Inspired by http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306

Example:

import urllib2_file
import urllib2

data = { 'foo':         'bar',
         'form_name':    open("/lib/libc.so.1")
        }
(send something like: 'Content-Disposition: form-data; name="form_name"; filename="form_name";' )

Or if you want to specify a different filename:
data = { 'foo':         'bar',
         'form_name':   { 'fd':          open('/lib/libresolv.so.2',
                          'filename':    'libresolv.so'}
        }
(send something like: 'Content-Disposition: form-data; name="form_name"; filename="libresolv.so";' )

u = urllib2.urlopen('http://site.com/path/upload.php', data)


THANKS to:
- bug fix: kosh @T aesaeion.com
- HTTPS support : Ryan Grow <ryangrow @T yahoo.com>
 - upload is now done with chunks (Adam Ambrose)
 - UTF-8 filenames are now allowed (Eli Golovinsky)
 - File object is no more mandatory, Object only needs to have seek() read() attributes (Eli Golovinsky)
 - StringIO workaround (Laurent Coustet), does not work with cStringIO

 Also modified by Adam Ambrose (aambrose @T pacbell.net) to write data in
chunks (hardcoded to CHUNK_SIZE for now), so the entire contents of the file
don't need to be kept in memory.

"""

__author__ = 'Fabien SEISEN'
__license__ = 'Python Software Foundation License version 2'
__url__ = 'http://fabien.seisen.org/python/'

import httplib
import mimetools
import mimetypes
import os
import os.path
import socket
import stat
import sys
import urllib
import urllib2

CHUNK_SIZE = 65536

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

# if sock is None, return the estimate size

def send_data(v_vars, v_files, boundary, sock=None):
    """Parse v_vars, v_files and create a buffer with HTTP multipart/form-data
    if sock is set, send data to it
        v_vars = {"key": "value"}
        v_files = {"filename" : open("path/to/file"}
    """

    buffer_len = 0
    for (k, v) in v_vars:
        buffer=''
        buffer += '--%s\r\n' % boundary
        buffer += 'Content-Disposition: form-data; name="%s"\r\n' % k
        buffer += '\r\n'
        buffer += v + '\r\n'
        if sock:
            sock.send(buffer)
        buffer_len += len(buffer)

    for (k, v) in v_files:
        name = k
        filename = k
        if isinstance(v, dict):
            if v.has_key('fd'):
                fd = v['fd']
            else:
                raise TypeError("if value is dict, it must have keys 'fd' and 'filename'")
            
            if v.has_key('filename'):
                filename = v['filename']
            else:
                raise TypeError("if value is dict, it must have keys 'fd' and 'filename'")
        else:
            fd = v

        if not hasattr(fd, 'seek'):
            raise TypeError("file descriptor MUST have seek attribute")

        if not hasattr(fd, 'read'):
            raise TypeError("file descriptor MUST have read attribute")

        fd.seek(0)
        if hasattr(fd, 'fileno'):
            # a File
            file_size = os.fstat(fd.fileno())[stat.ST_SIZE]
        else:
            # Final resort, read the entire message, and figure out the size
            file_size = 0
            while True:
                chunk = fd.read(CHUNK_SIZE)
                if chunk:
                    # It's not necessarily going to be CHUNK_SIZE large, since
                    # the last chunk is very likely < CHUNK_SIZE
                    file_size += len(chunk)
                else:
                    break
        fd.seek(0)

        if isinstance(filename, unicode):
            filename = filename.encode('UTF-8')
        buffer = ''
        buffer += '--%s\r\n' % boundary
        buffer += 'Content-Disposition: form-data; name="%s"; filename="%s";\r\n' \
                  % (name, filename)
        buffer += 'Content-Type: %s\r\n' % get_content_type(filename)
        buffer += 'Content-Length: %s\r\n' % file_size
        buffer += '\r\n'

        buffer_len += len(buffer)
        if sock:
            sock.send(buffer)
            if hasattr(fd, 'seek'):
                fd.seek(0)
        # read file only of sock is defined
        if sock:
            while True:
                chunk = fd.read(CHUNK_SIZE)
                if not chunk:
                    break
                if sock:
                    sock.send(chunk)
        buffer_len += file_size
    buffer = '\r\n'
    buffer += '--%s--\r\n' % boundary
    buffer += '\r\n'
    if sock:
        sock.send(buffer)
    buffer_len += len(buffer)
    return buffer_len

# mainly a copy of HTTPHandler from urllib2
class newHTTPHandler(urllib2.BaseHandler):
    def http_open(self, req):
        return self.do_open(httplib.HTTP, req)

    def do_open(self, http_class, req):
        data = req.get_data()
        v_files = []
        v_vars = []
        # mapping object (dict)
        if req.has_data() and type(data) != str:
            if hasattr(data, 'items'):
                data = data.items()
            else:
                try:
                    if len(data) and not isinstance(data[0], tuple):
                        raise TypeError
                except TypeError:
                    ty, va, tb = sys.exc_info()
                    raise TypeError, "not a valid non-string sequence or mapping object", tb
                
            for (k, v) in data:
                # if fd is provided with a filename
                if isinstance(v, dict):
                    if not v.has_key('fd'):
                        raise TypeError("if value is dict, it must have keys 'fd' and 'filename")
                    if not v.has_key('filename'):
                        raise TypeError("if value is dict, it must have keys 'fd' and 'filename")
                    v_files.append( (k, v) )
                elif hasattr(v, 'read'):
                    v_files.append( (k, v) )
                else:
                    v_vars.append( (k, v) )
        # no file ? convert to string
        if len(v_vars) > 0 and len(v_files) == 0:
            data = urllib.urlencode(v_vars)
            v_files = []
            v_vars = []
        host = req.get_host()
        if not host:
            raise urllib2.URLError('no host given')
        h = http_class(host) # will parse host:port
        if req.has_data():
            h.putrequest(req.get_method(), req.get_selector())
            if not 'Content-type' in req.headers:
                if len(v_files) > 0:
                    boundary = mimetools.choose_boundary()
                    l = send_data(v_vars, v_files, boundary)
                    h.putheader('Content-Type',
                                'multipart/form-data; boundary=%s' % boundary)
                    h.putheader('Content-length', str(l))
                else:
                    h.putheader('Content-type',
                                'application/x-www-form-urlencoded')
                    if not 'Content-length' in req.headers:
                        h.putheader('Content-length', '%d' % len(data))
        else:
            h.putrequest(req.get_method(), req.get_selector())

        scheme, sel = urllib.splittype(req.get_selector())
        sel_host, sel_path = urllib.splithost(sel)
        h.putheader('Host', sel_host or host)
        for name, value in self.parent.addheaders:
            name = name.capitalize()
            if name not in req.headers:
                h.putheader(name, value)
        for k, v in req.headers.items():
            h.putheader(k, v)
        # httplib will attempt to connect() here.  be prepared
        # to convert a socket error to a URLError.
        try:
            h.endheaders()
        except socket.error, err:
            raise urllib2.URLError(err)

        if req.has_data():
            if len(v_files) > 0:
                l = send_data(v_vars, v_files, boundary, h)
            elif len(v_vars) > 0:
                # if data is passed as dict ...
                data = urllib.urlencode(v_vars)
                h.send(data)
            else:
                # "normal" urllib2.urlopen()
                h.send(data)

        code, msg, hdrs = h.getreply()
        fp = h.getfile()
        if code == 200:
            resp = urllib.addinfourl(fp, hdrs, req.get_full_url())
            resp.code = code
            resp.msg = msg
            return resp
        else:
            return self.parent.error('http', req, fp, code, msg, hdrs)

urllib2._old_HTTPHandler = urllib2.HTTPHandler
urllib2.HTTPHandler = newHTTPHandler

class newHTTPSHandler(newHTTPHandler):
    def https_open(self, req):
        return self.do_open(httplib.HTTPS, req)
    
urllib2.HTTPSHandler = newHTTPSHandler

