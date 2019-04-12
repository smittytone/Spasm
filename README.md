# SPASM ‘Smittytone’s Primary 6809 ASeMbler’ 1.0.0 #

*spasm* is an assembler/disassembler for the Motorola 6809 microprocessor written in Python 3.

It was written to generate 6809 machine code for a separate processor emulation project. As such, it does not output files into a standard format, but in the form of JSON intended to be read by the emulator. The output file’s extension is `.6809`, but it is a text file containing a JSON object:

```json
{ "address" : <start_address_of_code>,
  "code"    : <string_of_assembled_code_bytes> }
```

A sample file, `sample01.6809`, is included with the repository.

Input is in the form of one or more `.asm` files which are text files containing the source code. For example:

```
; All comments go after a semi-colon

@tab_len    EQU %11111111       ; Table length in binary
@object     EQU $EE01           ; Object address in hex
@entlen     EQU $08             ; Table entry length
@search     LDB #@tab_len
            BEQ @exit           ; Exit if the table length is zero
            LDY #@object
            LDX #@store
@loop       PSHS B              ; start loop
            LDA #$2
@nextch     LDB A,Y
            CMPA B,X
            LEAX 3,X
            CMPA $2A,Y
            BNE @nexten         ; break out of loop
            DECB
            BPL @nextch
            PULS B
            LDA #$FF
            RTS
@nexten     PULS B
            DECB
            BEQ @exit
            LEAX @entlen,X       ; Interesting problem: this could add 0, 1 or 2
                                 ; bytes depending on the value of @entlen, which
                                 ; might not have been specified on the first pass
@exit       CLRA
@store      RMB @entlen
            RTS                  ; return
```

## Assembler Conventions ##

### Literals ###

Various literal types are supported. Literals are assumed to be decimal, but you can change this by using the following prefixes:

- `%` &mdash; a binary value, eg. `%10001111` (equals `0x8F`, 143).
- `'` &mdash; an 8-bit Ascii value, eg. `'A` (equals `0x41`, 65).
- `$` &mdash; a hexadecimal value, eg, `$FF00` (equals 65280).
    **Note** *spasm* can also read hexadecimal values prefixed with `0x` for modern users, but `$` is the classic Motorola prefix.

### Labels ###

As the above example shows, *spasm* supports the use of labels to represent values and memory locations (eg. for jumps and branches). All labels must be prefixed with `@`.

### Comments ###

Comments can be entered by prefixing them with a `;`. At this time, multi-line comment indicators have not yet been implemented.

### Directives ###

*spasm*  makes use of the following assembler directives (aka pseudo-ops):

- `EQU` &mdash; assign a value to a label, eg. `@label EQU 255`.
- `END` &mdash; optional end-of-code marker.
- `RMB` &mdash; reserve *n* memory bytes at this address, eg. `@label RMB 8 ; add 8 bytes for data storage`.
- `FCB` &mdash; store the following 8-bit value or values at this address, eg.
    - `@label FCB $FF         ; poke 255 to this address`.
    - `@label FCB $FF,$01,$02 ; poke 255, 0, 2 to sequential addresses from this`.
- `FDB` &mdash; store the following 16-bit value or values at this address, eg.
    - `@label FDB $FF00       ; poke 65280 to this address`.
    - `@label FDB $FF00,$FF01 ; poke 65280, 65281 to sequential addresses`.
    - **Note** The 6809 expects the most-significant byte at the lowest address.
- `ORG` &mdash; start assembling at the supplied address, eg. `@label ORG $3FFF ; continue assembling at address 16383`.

### Endianism ###

Motorola microprocessors are big endian, ie. the most-significant byte is written at the lowest  memory address and the least-significant byte is written at the highest address.

For example: store the 16-bit value `0x1A2B` from the address `0xFF00`:

```
0xFF00    0x1A
0xFF01    0x2B
```

## Sample Code ##

There are sample 6809 assembler programs and assembled `.6809` files in the [samples](/samples) folder.

## Command Line ##

*spasm* is a command line tool. It supports the following switches:

| Option | Alternative | Action |
| :-: | :-- | :-- |
| `-h` | `--help` | Print help information |
| `-v` | `--verbose` | Display extra information during assembly. This is the default |
| `-q` | `--quiet` | Display no extra information during assembly. This always overrides verbose mode |
| `-s` | `--start` | Set the start address of the assembled code, specified as a hex or decimal value.<br />**Note** You can use $ as a prefix for a hex value, but you will need to place the address in single quotes, eg. `spasm.py zzz.asm -s '$FF00'` to avoid confusing Bash |
| `-o` | `--output` | Cause the 6809 output file to be written and, optionally, name it. If you pass no name, the output file name will match the input file |
| `-l` | `--lower` | Display opcodes in lowercase |
| `-u` | `--upper` | Display opcodes in uppercase.<br />**Note** This and the above switch will overwrite each other; if both are called: the last one wins. If neither is used, the output matches the input |

## Release Notes ##

- 1.0.0 &mdash; *Unreleased*
    - Initial public release.

## Copyright And Licence ##

*spasm* is copyright © Tony Smith, 2019. The source code is released under the MIT licence.

The 6809 instruction set architecture is copyright © 1977 Motorola.
