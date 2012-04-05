#!/usr/bin/env python

import re
import argparse
import sys
import struct

opcodes = [
    'SET', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'SHL', 'SHR', 'AND', 'BOR',
    'XOR', 'IFE', 'IFN', 'IFG', 'IFB',
]
nonbasic_opcodes = [
    'JSR'
]
pointers = [
    'A', 'B', 'C', 'X', 'Y', 'Z', 'I', 'J',
    'POP', 'PEEK', 'PUSH', 'SP', 'PC', 'O',
]

oc = '|'.join(opcodes)  # (SET|ADD|SUB|...)
noc = '|'.join(nonbasic_opcodes)
deref_pattern = '\[\s*%s\s*\]'  # [ ? ]
hexa = '0x[0-9a-d]{1,4}'  # 0xbaba1
hexa_deref = deref_pattern % hexa  # [ 0xbaba1 ]
reg_pointers = '|'.join(pointers)  # A|B|C
reg_deref = '|'.join(deref_pattern % reg for reg in pointers[:8])  # [A]|[B]
hexa_plus_reg = '(%s)\s*\+\s*(%s)' % (hexa, '|'.join(pointers[:8]))  # 0xb1 + I
offset = deref_pattern % hexa_plus_reg  # [ 0xb1 + I ]
label = '\w+'
dec = '\d+'
op = '|'.join(
    '(%s)' % x for x in
    [hexa, hexa_deref, reg_pointers, reg_deref, offset, dec, label]
)
l_def = ':\w+'
row_pattern = '^\s*(%s)?\s*(((%s)\s+(%s)\s*,\s*(%s))|((%s)\s+(%s)))?\s*(;.*)?$'

re_row = re.compile(row_pattern % (l_def, oc, op, op, noc, op))


def emit_from_str(code):
    for line in code.split('\n'):
        parsed_line = re_row.match(line)
        if parsed_line is None:
            print 'error found on line: %s' % line
            exit(1)
        for token in emit_from_line(parsed_line.groups()):
            yield token


def emit_from_line(line):
    if line[0]:
        yield ('LABEL_DEF', line[0][1:])
    if line[3]:
        yield ('OPCODE', line[3])
        for token in emit_from_op(line[4:14]):
            yield token
        for token in emit_from_op(line[14:24]):
            yield token
    if line[24]:
        yield ('OPCODE_NB', line[25])
        for token in emit_from_op(line[26:36]):
            yield token
    if line[36]:
        yield ('COMMENT', line[36][1:])


def emit_from_op(op):
    if op[1]:
        yield ('CONST', int(op[1], 0))
    elif op[2]:
        yield ('CONST_DEREF', int(op[2][1:-1], 0))
    elif op[3]:
        yield ('REGISTRY', op[3])
    elif op[4]:
        yield ('REGISTRY_DEREF', op[4][1:-1])
    elif op[5]:
        yield ('OFFSET', (int(op[6], 0), op[7]))
    elif op[8]:
        yield ('CONST', int(op[8]))
    elif op[9]:
        yield ('LABEL_USE', op[9])


def compile(source):
    result = []
    emitter = emit_from_str(source)
    labels = {}
    labels_to_update = {}
    to_append = []

    def get_i(o_ttype, o_token):
        if o_ttype == 'CONST':
            i = o_token + 0x20
            if o_token > 0x1f:
                i = 0x1f
                to_append.append(o_token)
        elif o_ttype == 'CONST_DEREF':
            i = 0x1e
            to_append.append(o_token)
        elif o_ttype == 'REGISTRY':
            i = pointers.index(o_token)
            if i >= 8:
                i += 0x10
        elif o_ttype == 'REGISTRY_DEREF':
            i = pointers.index(o_token) + 0x08
        elif o_ttype == 'OFFSET':
            offset, reg = o_token
            i = pointers.index(reg) + 0x10
            to_append.append(offset)
        elif o_ttype == 'LABEL_USE':
            i = 0x1f
            addr = labels.get(o_token)
            if addr is None:
                pos = len(result) + 1
                labels_to_update.setdefault(o_token, []).append(pos)
            to_append.append(addr)
        return i

    for ttype, token in emitter:
        to_append[:] = []
        if ttype == 'LABEL_DEF':
            addr = labels[token] = len(result)
            for pos in labels_to_update.get(token, []):
                result[pos] = addr
        elif ttype == 'OPCODE':
            current_word = opcodes.index(token) + 1
            shift = 0
            for o_ttype, o_token in [emitter.next(), emitter.next()]:
                i = get_i(o_ttype, o_token)
                current_word += i << (4 + 6 * shift)
                shift += 1
            result.append(current_word)
            result.extend(to_append)
        elif ttype == 'OPCODE_NB':
            index = nonbasic_opcodes.index(token) + 1
            current_word = index << 4
            o_ttype, o_token = emitter.next()
            i = get_i(o_ttype, o_token)
            current_word += i << 10
            result.append(current_word)
            result.extend(to_append)
    return result


def pprint(words):
    f = '%0.4x'
    wrds = words
    if len(words) % 8:
        wrds = words + [0] * (8 - len(words) % 8)
    for x in range(0, len(wrds), 8):
        print f % x + ':', ' '.join(f % w for w in wrds[x:x + 8])


def main():
    parser = argparse.ArgumentParser(
        description='A simple Python-based DCPU assembly compiler'
     )
    parser.add_argument(
        'source', metavar='IN', type=str, nargs=1,
        help='file path of the file containing the assembly code'
    )
    parser.add_argument(
        'destination', metavar='OUT', type=str, nargs='?',
        help='file path where to store the binary code'
    )
    args = parser.parse_args()

    c = compile(open(args.source[0]).read())
    if args.destination is None:
        return pprint(c)

    assert sys.byteorder == 'little'
    out = open(args.destination, 'wb')
    c = [struct.pack('>H', b) for b in c]
    out.write(''.join(c))
    out.close()


if __name__ == '__main__':
    main()
