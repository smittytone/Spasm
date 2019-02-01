; p7-4
    CLRB
    LDA >$41
    CMPA #9
    BHI @dn
    LDX #@ss
    LDB A,X
@dn STB >$42
    ORG $20
@ss FCB $3F
