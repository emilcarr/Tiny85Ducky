import sys

keyMapUK =  [   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,         #0x00
                0xBB, 0xBA, 0x28, 0x28, 0x28, 0x28, 0x00, 0x00,         #0x08
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,         #0x10
                0x00, 0x00, 0x00, 0x29, 0x00, 0x00, 0x00, 0x00,         #0x18
                0x2C, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x24, 0x34,         #0x20
                0x26, 0x27, 0x25, 0x2E, 0x36, 0x2D, 0x37, 0x38,         #0x28
                0x27, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24,         #0x30
                0x25, 0x26, 0x33, 0x33, 0x36, 0x2E, 0x37, 0x38,         #0x38
                0x34, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,         #0x40
                0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12,         #0x48
                0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,         #0x50
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x23, 0x2D,         #0x58
                0x35, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,         #0x60
                0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12,         #0x60
                0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,         #0x70
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x32, 0x4C  ]       #0x78
                                                                        # ASCII Characters Mapped to UK Keyboard HID Scan codes. (see www.usb.org/developers/hidpage/Hut1_12v2.pdf Page 53)

shiftOnUK = '!"$%^&*()_+:<>?@{}|~ABCDEFGHIJKLMNOPQRSTUVWXYZ'            # ASCII Characters for which SHIFT must be held.

keyMapUS =  [   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,         #0x00
                0xBB, 0xBA, 0x28, 0x28, 0x28, 0x28, 0x00, 0x00,         #0x08
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,         #0x10
                0x00, 0x00, 0x00, 0x29, 0x00, 0x00, 0x00, 0x00,         #0x18
                0x2C, 0x1E, 0x34, 0x32, 0x21, 0x22, 0x24, 0x34,         #0x20
                0x26, 0x27, 0x25, 0x2E, 0x36, 0x2D, 0x37, 0x38,         #0x28
                0x27, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24,         #0x30
                0x25, 0x26, 0x33, 0x33, 0x36, 0x2E, 0x37, 0x38,         #0x38
                0x1F, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,         #0x40
                0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12,         #0x48
                0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,         #0x50
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x23, 0x2D,         #0x58
                0x35, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A,         #0x60
                0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12,         #0x68
                0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A,         #0x70
                0x1B, 0x1C, 0x1D, 0x2F, 0x31, 0x30, 0x35, 0x4C  ]       #0x78
                                                                        # US Map. Some of these are probably wrong, I don't have a US keyboard.
shiftOnUS = '!"$%^&*()_+:<>?@{}|~ABCDEFGHIJKLMNOPQRSTUVWXYZ'

keyMap = keyMapUK
shiftOn = shiftOnUK                                                     # Default to UK. US can be selected with "--us" in command line.

endianness = "little"                                                   # ATTiny85 uses little endian. I spent a long time debugging because of this...

def makeRegistrar():
    functionRegistry = {}
    syntaxRegistry = {}
    descriptionRegistry = {}
    def registrarWithArgs(name, description, syntax):    
        def registrar(func):
            functionRegistry[name] = func
            syntaxRegistry[name] = syntax
            descriptionRegistry[name] = description
            return func
        return registrar
    registrarWithArgs.all = functionRegistry
    registrarWithArgs.syntax = syntaxRegistry
    registrarWithArgs.description = descriptionRegistry
    return registrarWithArgs

currentLine = 0
currentByte = 0
markers = {"START":0}                                                   # Program locations of labels used by GOTO.

operations = makeRegistrar()                                            # All operations to be compiled should be iterables decorated with @operations

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
@operations("GOTO", "Jump to 16-bit program location.", "GOTO 0xllll (l = LOCATION) || GOTO marker")
def GOTO(args):
    yield bytes([0xE8])
    if args in markers:
        yield wordBytes(markers[args])
    else:
        yield wordBytes(int(args, 16))

# WAIT
@operations("WAIT", "Wait given amount of time in ms.", "WAIT 0xtttttttt")
def WAIT(args):
    yield bytes([0xE9])
    yield dwordBytes(int(args, 16))

# JUMP IF NUM LOCK
@operations("JMPIFN", "Jump to 16-bit program location, if NUM LOCK is set.", "JMPIFN 0xllll (l = LOCATION) || JMPIFN marker")
def JMPIFN(args):
    yield bytes([0xEA])
    if args in markers:
        yield wordBytes(markers[args])
    else:
        yield wordBytes(int(args, 16))

# JUMP IF CAPS
@operations("JMPIFC", "Jump to 16-bit program location, if CAPS LOCK is set.", "JMPIFC 0xllll (l = LOCATION) || JMPIFC marker")
def JMPIFC(args):
    yield bytes([0xEB])
    if args in markers:
        yield wordBytes(markers[args])
    else:
        yield wordBytes(int(args, 16))

# JUMP IF SCROLL LOCK
@operations("JMPIFS", "Jump to 16-bit program location, if SCROLL LOCK is set.", "JMPIFS 0xllll (l = LOCATION) || JMPIFS marker")
def JMPIFS(args):
    yield bytes([0xEC])
    if args in markers:
        yield wordBytes(markers[args])
    else:
        yield wordBytes(int(args, 16))

# SET MODIFIER ON
@operations("MODON", "Set given key modifier ON.", "MODON 0xmm (m = MODIFIER)")
def MODON(args):
    yield bytes([0xED, int(args, 16)])

# SET MODIFIER OFF
@operations("MODOFF", "Set given key modifier OFF.", "MODOFF 0xmm (m = MODIFIER)")
def MODOFF(args):
    yield bytes([0xEE, int(args, 16)])

# SHIFT
@operations("SHIFT", "Hold shift for the next character typed.", "SHIFT")
def SHIFT(args):
    if(len(args) == 0):
        yield bytes([0xEF])

# SET PIN DIRECTION
@operations("PINDR", "Set data direction of given pin on PORTB.", "PINDR 0xpd (p = PIN, d = DIRECTION)")
def PINDR(args):
    yield bytes([0xF0, int(args, 16)])
    
# SET PIN
@operations("SETPIN", "Set value of given pin on PORTB.", "SETPIN 0xpv (p = PIN, v = VALUE)")
def SETPIN(args):
    yield bytes([0xF1, int(args, 16)])
    
# JUMP IF PIN
@operations("JMPIFP", "Jump to 16-bit program location, if given pin on PORTB is HIGH.", "JMPIFP 0x0p 0xllll (p = PIN, l = LOCATION) || JMPIFP 0x0p marker (p = PIN)")
def JMPIFP(args):
    args = args.split(' ')
    print("JMPIFP args:", args)
    if len(args) < 2: raise Exception
    yield bytes([0xF2, int(args[0], 16)])
    if ' '.join(args[1:]) in markers:
        print("Going to marker: ", ' '.join(args[1:]))
        yield wordBytes(markers[args])
    else:
        if len(args) != 2: raise Exception
        yield wordBytes(int(args[1], 16))

@operations("TYPE", "Type given ASCII string as HID keycodes.", "TYPE str")
def TYPE(args):
    for c in args:
        if c in shiftOn:
            yield bytes([0xEF])
        yield bytes([keyMap[ord(c)]])

@operations("PRESS", "Press given HID keycodes.", "PRESS 0xkk ... (k = KEYCODE)")
def PRESS(args):
    for c in args.split(' '):
        yield bytes([int(args, 16)])

@operations(":", "Creates a pre-processor marker for use with GOTO and JMPIFx operations.", ": markername")
def createMarker(args):
    if args not in markers:
        markers[args] = currentByte
    return []

## This function yields assembled bytes, eg to be written to an output file.
# It reads from a file or input stream one line at a time and compiles to bytecodes.
def assemble(inputFile, verboseOutput=False):
    global currentLine,currentByte
    output = []
     
    for line in inputFile:                                              # Iterate through each operation
        line = line.strip().split(' ')
        op = line[0]
        args = ' '.join(line[1:])

        if op in operations.all:                                        # If the operation is recognized, yield all output from appropriate function.
            try:

                for b in operations.all[op](args):
                    yield b

                    if verboseOutput:
                        output.append((currentLine, ' '.join(line), currentByte, b.hex()))  # We want to print it with nice padding, so store for later.

                    currentByte += len(b)                               # Keep track of what byte the instruction is on.

            except Exception:                                           # If a function raises an Exception, assume SyntaxError.
                print("Syntax Error on line {0}: {1}. Syntax: {2}".format(currentLine, ' '.join(line), operations.syntax[op]))
                return

        else:
            print("Unknown Operation on line {0}: {1} is not a valid or recognised operation.".format(currentLine, op))
            return

        currentLine += 1

    if verboseOutput:                                                   # Print all compiled lines with nice padding
        pad = 0
        for l in output:
            if pad < len(l[1]):
                pad = len(l[1])
        
        print("LINE\tOPERATION\t" + ' '*(pad - 9) + "ADDRESS\tBYTE")
        for l in output:
            print(l[0], l[1], ' '*(pad - len(l[1])), l[2], l[3], sep="\t")


## This function reads the previously-generated bytecodes from a file and writes them into a C header file for use with the EEPROM flasher code.
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
        o.write("};\n")

## Just a hacky way to split --options from arguments, for command-line parsing
def argParse(args):
    options = []
    arguments = []
    for a in args:
        if a[:2] == "--":
            options.append(a)
        else:
            arguments.append(a)
    def names():
        return
    names.options = options
    names.arguments = arguments
    return names

if __name__ == "__main__":
    args = argParse(sys.argv[1:])

    if "--list-instructions" in args.options:
        pad = 0
        for op in operations.all:
            if pad < len(operations.description[op]):                   # Find the length of the longest description in order to print out nicely with consistent padding.
                pad = len(operations.description[op])

        for op in operations.all:
             print(op, operations.description[op], ' '*(pad - len(operations.description[op])), operations.syntax[op], sep="\t")

        sys.exit(0)

    if "--flasher" in args.options:
        if len(args.arguments) == 1:
            makeFlasherConfig(args.arguments[0])
            sys.exit(0)
        else:
            print("Usage: python assemble.py --flasher hexfile")
            sys.exit(1)
    
    if "--us" in args.options:
        keyMap = keyMapUS
        shiftOn = shiftOnUS

    if len(args.arguments) == 2:
        if "--verbose" in args.options:
            verboseOutput=True
        else:
            verboseOutput=False
        inputFile = open(args.arguments[0], 'r')
        outputFile = open(args.arguments[1], 'wb')

        for b in assemble(inputFile, verboseOutput):
            outputFile.write(b)

        print("{0} bytes compiled from {1} lines.".format(currentByte, currentLine))

        inputFile.close()
        outputFile.close()
        sys.exit(0)

    print("Usage: python assemble.py [--flasher hexfile] [--list-instructions] [--verbose] [inputfile outputfile]")
    sys.exit(1)
