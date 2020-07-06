     IMPLICIT INTEGER(A-Z)
     OPEN(UNIT=1, FILE='advent.dat', STATUS='OLD')
     READ(1, 50) X, EXTRA
50   FORMAT(I2, A)
     PRINT 100, X, EXTRA
100  FORMAT('Section: ' I2, ' *', A, '*')
     READ(1, 150) Y, WORDS
150  FORMAT(I3, A)


A = 1
B = 2
PRINT 500, A, B
500 FORMAT ('A = ', I2, '. B = ', I2)
END
