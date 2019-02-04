; p7-4
    CLRB
    LDA >$41
    CMPA #9
    BHI @dn
    LDX #@ss
    LDB A,X
@dn STB >$42
    ORG $20
@ss FCB $3F,$4F,$5F,$6F
    ORG $40
@ds FDB $FF00,$FF01,$FF02,$FF03,$FF04

