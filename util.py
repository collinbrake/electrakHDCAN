import math

# This function reverses in range [bitCount, 0]
def reverse_bit(num, bitCount):
    result = 0
    if num == 0:
        return result
    temp = num
    while temp:
        result = (result << 1) + (temp & 1)
        temp >>= 1

    sigBits =math.ceil(math.log2(num)) 
    return result << (bitCount - sigBits) # Account for leading zeros