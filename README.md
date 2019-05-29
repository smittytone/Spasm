# SPASM ‘Smittytone’s Primary 6809 ASeMbler’ 1.2.0 #

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
- `$` &mdash; a hexadecimal value, eg, `$FF00` (equals 65280).<br />**Note** *spasm* can also read hexadecimal values prefixed with `0x` for modern users, but `$` is the classic Motorola prefix.

### Labels ###

As the above example shows, *spasm* supports the use of labels to represent values and memory locations (eg. for jumps and branches). All labels **must** be prefixed with `@`.

### Comments ###

Comments can be entered by prefixing them with a `;` or `*` (for DREAM fans). At this time, multi-line comment indicators have not yet been implemented.

### Directives ###

*spasm*  makes use of the following assembler directives (aka pseudo-ops):

- `EQU` &mdash; assign a value to a label, eg. `@label EQU 255`.
- `END` &mdash; optional end-of-code marker.
- `RMB` &mdash; reserve *n* memory bytes at this address, eg. `@label RMB 8 ; add 8 bytes for data storage`.
- `FCB` &mdash; store the following 8-bit value or values at this address, eg.
    - `@label FCB $FF          ; poke 255 to this address`.
    - `@label FCB $FF,$01,$02  ; poke 255, 0, 2 to sequential addresses from this`.
- `FCC` &mdash; store the following string at this address, eg.
    - `@label FCC "Message"    ; poke 77,101,115,115,97,103,101 to sequential addresses`.
- `FDB` &mdash; store the following 16-bit value or values at this address, eg.
    - `@label FDB $FF00        ; poke 65280 to this address`.
    - `@label FDB $FF00,$FF01  ; poke 65280, 65281 to sequential addresses`.
    - **Note** The 6809 expects the most-significant byte at the lowest address.
- `ORG` &mdash; continue assembly at the supplied address, eg. `@label ORG $3FFF ; continue assembly at address 16383`.

### Endianism ###

Motorola microprocessors are big endian, ie. the most-significant byte is written at the lowest  memory address and the least-significant byte is written at the highest address.

For example: store the 16-bit value `0x1A2B` from the address `0xFF00`:

```
0xFF00    0x1A
0xFF01    0x2B
```

## Sample Code ##

There are sample 6809 assembler programs and assembled `.6809` files in the [samples](/samples) folder.

## Disassembly ##

*spasm* will disassemble `.6809` files, using the start address included in the file. It can also disassemble `.rom` files. Since these do not include address information, you can use the `-s` switch to set the effective address of the first byte in the `.rom` file. Because you may not wish to disassemble the entire file, you can use the `-b` switch to set the address from which disassembly will begin, and `-n` to set the number of bytes you want to disassemble.

For example, if you have a 16KB ROM that is expected to be placed at `0x8000` in the 6809 memory map, you set the start address (with `-s`) to `0x8000`. However, you only want to disassemble from `0x9000`, so you use `-b` to set the base address to `0x9000`. You only want to disassemble the 128 bytes at `0x9000`, so you use `-n 128`:

```bash
./spasm.py my_rom.rom -s 0x8000 -b 0x9000 -n 128
```

This might output:

```
Address   Operation       Bytes
-------------------------------
0x9000    BNE    $9008    2606
0x9002    CMPB   #84      C184
0x9004    BNE    $900C    2606
0x9006    LDA    #3A      863A
0x9008    STD    ,U++     EDC1
0x900A    BRA    $8FA1    2094
0x900C    STB    ,U+      E7C0
0x900E    CMPB   #86      C186
0x9010    BNE    $9014    2602
0x9012    INC    >44      0C44
0x9014    CMPB   #82      C182
0x9016    BEQ    $8FC3    27AA
0x9018    BRA    $8FA1    2086
0x901A    LDU    #011B    CE011B
0x901D    COM    >41      0341
0x901F    BNE    $8FE2    26C0
0x9021    PULS   X,U      3550
0x9023    LDA    ,X+      A680
0x9025    STA    ,U+      A7C0
0x9027    JSR    8ADF     BD8ADF
0x902A    BLO    $9019    25EC
0x902C    COM    >43      0343
0x902E    BRA    $9019    20E8
0x9030    INC    >42      0C42
0x9032    DECA            4A
0x9033    BEQ    $8FE4    27AE
0x9035    LEAY   $0F,Y    313F
0x9037    LDB    ,Y+      E6A0
0x9039    BPL    $9038    2AFC
0x903B    BRA    $8FED    20AF
0x903D    BEQ    $90A1    2762
0x903F    BSR    $9044    8D03
0x9041    CLR    >6F      0F6F
0x9043    RTS             39
0x9044    CMPA   #40      8140
0x9046    BNE    $904D    2605
0x9048    JSR    B786     BDB786
0x904B    BRA    $9057    200A
0x904D    CMPA   #23      8123
0x904F    BNE    $905E    260D
0x9051    JSR    B7D7     BDB7D7
0x9054    JSR    B63C     BDB63C
0x9057    JSR    >A5      9DA5
0x9059    BEQ    $90A1    2746
0x905B    JSR    89AA     BD89AA
0x905E    CMPA   #CD      81CD
0x9060    LBEQ   $A224    102711C1
0x9063    BEQ    $90AD    2748
0x9065    CMPA   #BB      81BB
0x9067    BEQ    $90C6    275D
0x9069    CMPA   #2C      812C
0x906B    BEQ    $90AE    2741
0x906D    CMPA   #3B      813B
0x906F    BEQ    $90DF    276E
0x9071    JSR    8887     BD8887
0x9074    LDA    >06      9606
0x9076    PSHS   A        3402
0x9078    BNE    $9080    2606
0x907A    JSR    9587     BD9587
0x907D    JSR    8C59     BD8C59
```

The `-b` and `-n` switches can be used when you are disassembling `.6809` files, but the code’s start address will always be taken from the file, not an address set with `-s`.

See below for a full list of *spasm* switches.

## Command Line ##

*spasm* is a command line tool. It supports the following switches:

| Option | Alternative | Action |
| :-: | --- | --- |
| `-h` | `--help`        | Print help information |
| `-v` | `--version`     | Display *spasm* version information |
| `-q` | `--quiet`       | Display no extra information during assembly. This overrides verbose mode,<br />which is the default |
| `-s` | `--start`       | Set the start address of the assembled code, specified as a hex or decimal value.<br />**Note** You can use $ as a prefix for a hex value, but you will need to place<br />the address in single quotes, eg. `spasm.py zzz.asm -s '$FF00'` to avoid confusing Bash |
| `-b` | `--baseaddress` | Set the base address for disassembled code, specified as a hex or decimal value.<br />Ignored during assembly |
| `-n` | `--numbytes`    | Set the number of bytes to disassemble, specified as a hex or decimal value.<br />Ignored during assembly |
| `-o` | `--output`      | Cause the 6809 output file to be written and, optionally, name it. If you pass no name,<br />the output file name will match that of the input file but with a `.6809` extension |
| `-l` | `--lower`       | Display opcodes in lowercase |
| `-u` | `--upper`       | Display opcodes in uppercase.<br />**Note** This and the above switch will overwrite each other; if both are called:<br />the last one wins. If neither is used, the output matches the input |

## Release Notes ##

- 1.2.0 &mdash; *unreleased*
    - *Improvements*
        - Fully support `ORG` directive: assemble code into multiple chunks.
        - Add support for `FCC` directive: assemble code Ascii strings to bytes.
        - Improve operation of `FCB` and `FDB` directives.
        - `.6809` files' *code* field now contains a string of two-character hex values.
        - Change `-v` switch to present version info (as verbose mode is default).
    - *Bug Fixes*
        - Handle negative operands correctly.
        - Handle indirect extended addressing correctly.
        - Check ops that expect an 8-bit value don't get a 16-bit value.
        - Correct address increments during disassembly of extended opcodes.
- 1.1.0 &mdash; *30 April 2019*
    - *Improvements*
        - Add disassembly of `.rom` files.
        - Add `-n` switch to set number of bytes of code to be disassembled.
        - Add `-b` switch to set base address of disassembly.
- 1.0.0 &mdash; *12 April 2019*
    - Initial public release.

## Copyright And Licence ##

*spasm* is copyright © Tony Smith, 2019. The source code is released under the MIT licence.

The 6809 instruction set architecture is copyright © 1977 Motorola/Freescale/NXP.
