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
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x32, 0x4C  ]       # ASCII Characters Mapped to UK Keyboard HID Scan codes

shiftOnUK = '!"$%^&*()_+:<>?@{}|~ABCDEFGHIJKLMNOPQRSTUVWXYZ'            # ASCII Characters for which SHIFT must be held

keyMap = keyMapUK
shiftOn = shiftOnUK                                                     # You can set which keymap to use in this way

endianness = "little"                                                   # ATTiny85 uses little endian. I spent a long time debugging because of this...

def makeRegistrar():
    functionRegistry = {}
    syntaxRegistry = {}
    def registrarWithSyntax(syntax):    
        def registrar(func):
            functionRegistry[func.__name__] = func
            syntaxRegistry[func.__name__] = syntax
            return func
        return registrar
    registrarWithSyntax.all = functionRegistry
    registrarWithSyntax.syntax = syntaxRegistry
    return registrarWithSyntax

currentByte = 0
markers = {"START":0}                                                   # Program locations of labels used by GOTO.

operations = makeRegistrar()                                            # All operations to be compiled should be decorated with @operations

def dwordBytes(x):                                                      # Convert an int into a dword. Ensures endianness is correct.
    if x > 0xFFFFFFFF:
        raise OverflowError
    if endianness == "big":
        return bytes([(x & 0xFF000000) >> 24, (x & 0xFF0000) >> 16, (x & 0xFF00) >> 8, (x & 0xFF)])
    elif endianness == "little":
        return bytes([(x & 0xFF), (x & 0xFF00) >> 8, (x & 0xFF0000) >> 16, (x & 0xFF000000) >> 24])


def wordBytes(x):                                                       # Convert an int into a word.
    if x > 0xFFFF:
        raise OverflowError
    if endianness == "big":
        return bytes([(x & 0xFF00) >> 8, (x & 0xFF)])
    elif endianness == "little":
        return bytes([(x & 0xFF), (x & 0xFF00) >> 8])

def byte(x):                                                            # Convert int into 8-bit byte
    if x > 0xFF:
        raise OverflowError
    return bytes([x & 0xFF])

# GOTO
@operations("GOTO")
def GOTO(args):
    yield bytes([0xE8])
    if args in markers:
        yield wordBytes(markers[args])
        print("found marker for " + args)
        return
    try:
        yield wordBytes(int(args, 16))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "GOTO expects 16-bit hexadecimal value. Syntax: GOTO 0xllll (l = LOCATION)")

# WAIT
@operations("WAIT expects 32-bit hexademical value. Syntax: WAIT 0xtttttttt")
def WAIT(args):
    yield bytes([0xE9])
    yield dwordBytes(int(args, 16))

# JUMP IF NUM LOCK
@operations("JUMP IF NUM LOCK")
def JMPIFN(args):
    yield bytes([0xEA])
    try:
        yield wordBytes(int(args, 16))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "JMPIFN expect 16-bit hexadecimal value. Syntax: JMPIFN 0xllll (l = LOCATION)")

# JUMP IF CAPS
@operations("JUMP IF CAPS")
def JMPIFC(args):
    yield bytes([0xEB])
    try:
        yield wordBytes(int(args, 16))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "JMPIFC expect hexadecimal value. Syntax: JMPIFC 0xllll (l = LOCATION)")

# JUMP IF SCROLL LOCK
@operations("JUMP IF SCROLL LOCK")
def JMPIFS(args):
    yield bytes([0xEC])
    try:
        yield wordBytes(int(args, 16))
    except (ValueError, OverflowError):
        raise Exception("SyntaxError", "JMPIFS expect hexadecimal value. Syntax: JMPIFS 0xllll (l = LOCATION)")

# SET MODIFIER ON
@operations("SET MODIFIER ON")
def MODON(args):
    try:
        yield bytes([0xED, int(args, 16)])
    except ValueError:
        raise Exception("SyntaxError", "MODON expects hexadecimal value. Syntax: MODON 0xmm (m = MODIFIER)")

# SET MODIFIER OFF
@operations("SET MODIFIER OFF")
def MODOFF(args):
    try:
        yield bytes([0xEE, int(args, 16)])
    except ValueError:
        raise Exception("SyntaxError", "MODOFF expects hexadecimal value. Syntax: MODOFF 0xmm (m = MODIFIER)")

# SHIFT
@operations("SHIFT")
def SHIFT(args):
    if(len(args) == 0):
        yield bytes([0xEF])
    else:
        raise Exception("SyntaxError", "Unknown argument for SHIFT. Syntax: SHIFT")

# SET PIN DIRECTION
@operations("SET PIN DIRECTION")
def PINDR(args):
    try:
        yield bytes([0xF0, int(args, 16)])
    except ValueError:
        raise Exception("SyntaxError", "PINDR expects hexadecimal value. Syntax: PINDR 0xpd (p = PIN, d = DIRECTION)")

# SET PIN
@operations("SET PIN")
def SETPIN(args):
    try:
        yield bytes([0xF1, int(args, 16)])
    except ValueError:
        raise Exception("SyntaxError", "PINDR expects hexadecimal value. Syntax: PINDR 0xpv (p = PIN, v = VALUE")

# JUMP IF PIN
@operations("JUMP IF PIN")
def JMPIFP(args):
    args = args.split(' ')
    try:
        if len(args) != 2: raise ValueError
        yield bytes([0xF2, int(args[0], 16)])
        yield wordBytes(int(args[1], 16))
    except ValueError:
        raise Exception("SyntaxError", "JMPIFP expects two hexadeimal values. Syntax: 0x0p 0xllll (p = PIN, l = LOCATION)")

@operations("TYPE STRING")
def TYPE(args):
    for c in args:
        if c in shiftOn:
            yield bytes([0xEF])
        yield bytes([keyMap[ord(c)]])

@operations("PRESS")
def PRESS(args):
    for c in args.split(' '):
        try:
            yield bytes([int(args, 16)])
        except ValueError:
            raise Exception("SyntaxError", "PRESS expects hexadecimal value. Syntax: PRESS 0xkk (k = KEYCODE)")

def createMarker(args):
    if args not in markers:
        markers[args] = currentByte

def assemble(inputFile):
    global currentByte
    for line in inputFile:
        line = line.split(' ')
        op = line[0]
        args = ' '.join(line[1:])
        if op[0] == ':':
            createMarker(args)
        elif op in operations.all:
            try:
                for b in operations.all[op](args):
                    yield b
                    currentByte += len(b)
            except Exception:
                print("Syntax Error: {0}".format(operations.syntax[op]))
                return
        else:
            print("UnknownOperation: {0} is not a valid or recognised operation.".format(op))
            return

def makeFlasherConfig(inputFile):
    import struct
    with open(inputFile, 'rb') as i, open("program.h", 'w') as o:
        i.seek(0,2)
        o.write("#define PROGSIZE {0} \nuint8_t PROG[PROGSIZE] = {{".format( i.tell() ) )
        i.seek(0,0)
        byte = i.read(1)
        p = 0
        while byte != b'':
            if p == 0:
                o.write('{0}'.format( struct.unpack('<B', byte)[0] ) )
            else:
                o.write(', {0}'.format( struct.unpack('<B', byte)[0] ) )
            p += 1;
            byte = i.read(1)
        o.write("};")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        if("--flasher" == sys.argv[1]):
            makeFlasherConfig(sys.argv[2])
            sys.exit(0)
        inputFile = open(sys.argv[1], 'r')
        outputFile = open(sys.argv[2], 'wb')
    else:
        print("Usage: python assemble.py inputfile outputfile")
        sys.exit(1);
    
    for b in assemble(inputFile):
        outputFile.write(b)
    
    inputFile.close()
    outputFile.close()
    sys.exit(0)
        
