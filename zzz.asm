    LDX #$42
    CLR >$40
@ck LDA ,X
    LSRA
    LSRA
    LSRA
    LSRA
    TFR A,B
    ADDA >$40
    DAA
    STA >$40
    TFR B,A
    ADDA >$40
    DAA
    ADDA ,x+
    DAA
    STA >$40
    DEC >$41
    BNE @ck
    ANDA #%00001111
    STA >$40
    SWI
        