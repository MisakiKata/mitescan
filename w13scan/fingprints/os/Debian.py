#!/usr/bin/env python 
# -*- coding:utf-8 -*-
#
# @name:    Debian
# @author:  w8ay

from re import search, I, compile, error

from w13scan.lib.core.enums import OS


def _prepare_pattern(pattern):
    """
    Strip out key:value pairs from the pattern and compile the regular
    expression.
    """
    regex, _, rest = pattern.partition('\;')
    try:
        return compile(regex, I)
    except error as e:
        return compile(r'(?!x)x')


def fingerprint(headers, content):
    _ = False
    if 'server' in headers.keys():
        _ |= search(r"Debian", headers["server"], I) is not None
    if 'x-powered-by' in headers.keys():
        _ |= search(r"(?:Debian|dotdeb|(sarge|etch|lenny|squeeze|wheezy|jessie))\;version:\1", headers["x-powered-by"],
                    I) is not None

    if _: return "Debian", OS.LINUX
