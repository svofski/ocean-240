        .project %(label)s.ok

SCROLL_V        equ     0C0h
BANKING         equ     0C1h
SCROLL_VH       equ     0C2h
VIDEO           equ     0E1h
ENROM           equ     0x10
SCREEN          equ     0c000h

SCREEN_ROW      equ	0
SCREEN_COL      equ	0

        org     100h

        mvi     a, 40h+%(palette_index)d          ; палитра
        out     VIDEO
        call    ResetScroll
        call    ClearScreen
        call    DrawBitmap
        ret


DrawBitmap:
        di
        mvi a, ENROM
        out BANKING

        lxi b, %(label)s
        mvi h, (SCREEN >> 8)+SCREEN_COL
        dcr h
        lda %(label)s_nc
        mov d, a
        
drwbmp_nextcol
        inr h
        mvi l, SCREEN_ROW
        
        lda %(label)s_nr
        mov e, a
        
drwbmp_nextrow
        ldax b
        mov m, a
        inr l
        inx b
        
        dcr e
        jnz drwbmp_nextrow
        dcr d
        jnz drwbmp_nextcol

        xra     a
        out     BANKING
        ei
        ret


; Установить нулевые смещения для вертикальной и горизонтальной прокруток        
ResetScroll
        xra     a
        out     SCROLL_V
        out     SCROLL_VH
        ret
        
ClearScreen
        di
        mvi     a, ENROM
        out     BANKING
        
        lxi     h, SCREEN
        lxi     b, 256*64
        
Cls     mvi     m, 0
        inx     h
        dcx     b
        mov     a, b
        ora     c
        jnz     Cls
        
        xra     a
        out     BANKING
        ei
        ret

%(dbtext)s

