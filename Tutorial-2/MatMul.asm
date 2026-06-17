// ── Init A (row-major) ───────────────────────────────────────
// Row 0: 2 3 1
@2
D=A
@16
M=D

@3
D=A
@17
M=D

@1
D=A
@18
M=D

// Row 1: 4 0 5
@4
D=A
@19
M=D

@0
D=A
@20
M=D

@5
D=A
@21
M=D

// Row 2: 1 2 3
@1
D=A
@22
M=D

@2
D=A
@23
M=D

@3
D=A
@24
M=D

// ── Init B (column-major) ────────────────────────────────────
// Col 0: 5 3 8
@5
D=A
@25
M=D

@3
D=A
@26
M=D

@8
D=A
@27
M=D

// Col 1: 7 1 4
@7
D=A
@28
M=D

@1
D=A
@29
M=D

@4
D=A
@30
M=D

// Col 2: 2 6 0
@2
D=A
@31
M=D

@6
D=A
@32
M=D

@0
D=A
@33
M=D

// ── Zero out C (RAM[34..42]) ─────────────────────────────────
@0
D=A
@34
M=D
@35
M=D
@36
M=D
@37
M=D
@38
M=D
@39
M=D
@40
M=D
@41
M=D
@42
M=D

// ── i = 0 ────────────────────────────────────────────────────
@0
D=A
@R0
M=D

(LOOP_I)
    @R0
    D=M
    @3
    D=D-A
    @END
    D;JEQ

    @0
    D=A
    @R1
    M=D

    (LOOP_J)
        @R1
        D=M
        @3
        D=D-A
        @NEXT_I
        D;JEQ

        @0
        D=A
        @R3
        M=D

        @0
        D=A
        @R2
        M=D

        (LOOP_K)
            @R2
            D=M
            @3
            D=D-A
            @STORE_C
            D;JEQ

            // load A[i][k] = RAM[16 + 3i + k]
            @R0
            D=M
            @R0
            D=D+M
            @R0
            D=D+M
            @16
            D=D+A
            @R2
            A=D+M
            D=M
            @R13
            M=D

            // load B[k][j] = RAM[25 + 3j + k]
            @R1
            D=M
            @R1
            D=D+M
            @R1
            D=D+M
            @25
            D=D+A
            @R2
            A=D+M
            D=M
            @R14
            M=D

            @MULTIPLY
            0;JMP
            (MULTIPLY_RETURN)

            @R15
            D=M
            @R3
            M=D+M

            @R2
            M=M+1

            @LOOP_K
            0;JMP

        (STORE_C)
        // C[i][j] = RAM[34 + 3i + j]
        @R0
        D=M
        @R0
        D=D+M
        @R0
        D=D+M
        @34
        D=D+A
        @R1
        D=D+M
        @R7
        M=D

        @R3
        D=M
        @R7
        A=M
        M=D

        @R1
        M=M+1

        @LOOP_J
        0;JMP

    (NEXT_I)
    @R0
    M=M+1

    @LOOP_I
    0;JMP

(END)
@END
0;JMP

// MULTIPLY: R13 * R14 -> R15  (repeated addition)
(MULTIPLY)
    @0
    D=A
    @R15
    M=D

    @1
    D=A
    @43
    M=D

    @R13
    D=M
    @MUL_X_POS
    D;JGE
    @R13
    M=-M
    @43
    M=-M
    (MUL_X_POS)

    @R14
    D=M
    @MUL_Y_POS
    D;JGE
    @R14
    M=-M
    @43
    M=-M
    (MUL_Y_POS)

    (MUL_LOOP)
        @R14
        D=M
        @MUL_DONE
        D;JEQ

        @R13
        D=M
        @R15
        M=D+M

        @R14
        M=M-1

        @MUL_LOOP
        0;JMP

    (MUL_DONE)
    @43
    D=M
    @MUL_POSITIVE
    D;JGT
    @R15
    M=-M
    (MUL_POSITIVE)

    @MULTIPLY_RETURN
    0;JMP