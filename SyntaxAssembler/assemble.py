import sys

keyMapUK =  [   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                0xBB, 0xBA, 0x28, 0x28, 0x28, 0x28, 0x00, 0x00, 
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x29, 0x00, 0x00, 0x00, 0x00,
                0x2C, 0x1E, 0x1F, 0x32, 0x21, 0x22, 0x24, 0x34,
                0x26, 0x27, 0x25, 0x2E, 0x36, 0x2D, 0x37, 0x38,
                0x27, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 
                0x25, 0x26, 0x33, 0x33, 0x36, 0x2E, 0x37, 0x38,
                0x34, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,
                0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12,
                0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x23, 0x2D, 
                0x35, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,
                0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12,
                0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x32, 0x4C  ]

shiftOnUK = '!"$%^&*()_+:<>?@{}|~ABCDEFGHIJKLMNOPQRSTUVWXYZ'

keyMap = keyMapUK
shiftOn = shiftOnUK

length = 0
lineNumber = 0

def makeRegistrar():
    registry = {}
    def registrar(func):
        registry[func.__name__] = func
        return func
    registrar.all = registry
    return registrar

operations = makeRegistrar()

def dwordBytes(x):
    if x > 0xFFFFFFFF:
        raise OverflowError
    return bytes([(x & 0xFF000000) >> 24, (x & 0xFF0000) >> 16, (x & 0xFF00) >> 8, (x & 0xFF)])

def wordBytes(x):
    if x > 0xFFFF:
        raise OverflowError
    return bytes([(x & 0xFF00) >> 8, (x & 0xFF)])

@operations
def GOTO(args):
    yield bytes([0xE8])
    try:
        yield wordBytes(int(args))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "GOTO expects integer value. Syntax: GOTO [16-bit location]")

@operations
def WAIT(args):
    yield bytes([0xE9])
    try:
        yield dwordBytes(int(args))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "WAIT expects integer value. Syntax: WAIT [32-bit time in ms]")

@operations
def JMPIFN(args):
    yield bytes([0xEA])
    try:
        yield wordBytes(int(args))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "JMPIFN expect integer value. Syntax: JMPIFN [16-bit location]")

@operations
def JMPIFC(args):
    yield bytes([0xEB])
    try:
        yield wordBytes(int(args))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "JMPIFC expect integer value. Syntax: JMPIFC [16-bit location]")

@operations
def JMPIFS(args):
    yield bytes([0xEC])
    try:
        yield wordBytes(int(args))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "JMPIFS expect integer value. Syntax: JMPIFS [16-bit location]")

@operations
def MODON(args):
    try:
        yield bytes([0xED, int(args)])
    except ValueError:
        raise Exception("SyntaxError", "MODON expects integer value. Syntax: MODON [modifier]")

@operations
def MODON(args):
    try:
        yield bytes([0xEE, int(args)])
    except ValueError:
        raise Exception("SyntaxError", "MODOFF expects integer value. Syntax: MODOFF [modifier]")

@operations
def SHIFT(args):
    if(len(args) > 0):
        yield bytes([0xEF])

def assemble(inputFile):
    for line in inputFile:
        op = line.split(' ')[0]
        args = ' '.join(line.split(' ')[1:])
        #lineNumber += 1
        if op in operations.all:
            for b in operations.all[op](args):
                yield b
        elif op == "TYPE":
            for c in line[5:]:
                if c in shiftOn:
                    yield bytes([0xEF])
                yield bytes([keyMap[ord(c)]])

if __name__ == "__main__":
    if len(sys.argv) == 3:
        inputFile = open(sys.argv[1], 'r')
        outputFile = open(sys.argv[2], 'wb')
    else:
        print("Usage: python assemble.py inputfile outputfile")
        sys.exit(1);
    
    try:
        for b in assemble(inputFile):
            outputFile.write(b)
    except Exception as inst:
        print("Exception on line %i: " % lineNumber)
        print("%s: %s" % inst.args)
        print(inst)
        sys.exit(1);

    sys.exit(0);
        
