import re

# TODO:
# add labels
# add non-basic support

opcodes = [
    'SET', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'SHL', 'SHR', 'AND', 'BOR',
    'XOR', 'IFE', 'IFN', 'IFG', 'IFB',
]
pointers = [
    'A', 'B', 'C', 'X', 'Y', 'Z', 'I', 'J',
    'POP', 'PEEK', 'PUSH', 'SP', 'PC', 'O',
]

oc = '|'.join(opcodes) # (SET|ADD|SUB|...)
deref_pattern = '\[\s*%s\s*\]' # [ ? ]
hexa = '0x[0-9a-d]{1,4}' # 0xbaba1
hexa_deref =  deref_pattern % hexa # [ 0xbaba1 ]
reg_pointers = '|'.join(pointers) # A|B|C
reg_deref = '|'.join(deref_pattern % reg for reg in pointers[:8]) # [A]|[B]
hexa_plus_reg = '(%s)\s*\+\s*(%s)' % (hexa, '|'.join(pointers[:8])) # 0xb1 + I
offset = deref_pattern % hexa_plus_reg # [ 0xb1 + I ]
label = '\w+'
dec = '\d+'
op = '|'.join(
    '(%s)' % x for x in
    [hexa, hexa_deref, reg_pointers, reg_deref, offset, dec, label]
)
l_def = ':\w+'
row_pattern = '^\s*(%s)?\s*((%s)\s+(%s)\s*,\s*(%s))?\s*(;.*)?$'
re_row = re.compile(row_pattern % (l_def, oc, op, op))


def emit_from_str(code):
    for line in code.split('\n'):
        parsed_line = re_row.match(line)
        if parsed_line is None:
            print 'error found on line: %s' % line
            exit(1)
        print line
        for token in emit_from_line(parsed_line.groups()):
            yield token


def emit_from_line(line):
    if line[0]:
        yield ('LABEL_DEF', line[0][1:])
    if line[2]:
        yield ('OPCODE', line[2])
        for token in emit_from_op(line[3:13]):
            yield token
        for token in emit_from_op(line[13:23]):
            yield token
    if line[21]:
        yield ('COMMENT', line[21][1:])


def emit_from_op(op):
    if op[1]:
        yield ('CONST', int(op[1], 0))
    if op[2]:
        yield ('CONST_DEREF', int(op[2][1:-1], 0))
    if op[3]:
        yield ('REGISTRY', op[3])
    if op[4]:
        yield ('REGISTRY_DEREF', op[4][1:-1])
    if op[5]:
        yield ('OFFSET', (int(op[6], 0), op[7]))
    if op[8]:
        yield ('CONST', int(op[8]))
    if op[9]:
        yield ('LABEL_USE', op[9])


def compile(source):
    result = []
    emitter = emit_from_str(source)
    for ttype, token in emitter:
        to_append = []
        if ttype == 'OPCODE':
            current_word = opcodes.index(token) + 1
            shift = 0
            for o_ttype, o_token in [emitter.next(), emitter.next()]:
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
                current_word += i << (4 + 6 * shift)
                shift += 1
            result.append(current_word)
            if to_append:
                result.extend(to_append)
    return '\t'.join([hex(r) for r in result])


if __name__ == '__main__':
    code = """
        SET A, 0x30
        SET [0x1000], 0x20
        SUB A, [0x1000]
        SET A, 0x2000
        SET [0x2000+I], [A]
        SET PC, POP
        IFN A, 0x10              ; c00d 
        IFN I, 0x0               ; 806d
        SHL X, 0x4               ; 9037
        SHL X, 4                 ; 9037
        IFN I, 0                 ; 806d
        IFN I, 10000
    """
    print compile(code)
