@search     LDB #255
            TFR X,B
            LDY #$EE01
            PSHS CC,A,X,Y
            BEQ @search
            RTS
            