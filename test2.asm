        org $1000
@strt   lda #128
        ldx #$0400
@clr    sta ,x+
        cmpx #$0600
        bne @clr
@strt2  lda #32
        ldx #$0400
@clr2   sta ,x+
        inca
        bne @up
        lda #32
        jmp @up
        org $1050
@up     cmpx #$05FE
        ble @clr2
        rts
