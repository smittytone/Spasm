@search     LDB #255
            TFR B,CC
            LDY #$EE01
            PSHS CC,A,X,Y
            BEQ @search
            RTS

