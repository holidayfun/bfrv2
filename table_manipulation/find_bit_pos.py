
bitstring_len = 64

for i in range(0, bitstring_len):
    bitstring = ("{0:0" + str(bitstring_len) + "d}").format(10**i)
    prefix_len = bitstring_len - i
    output = "table_add find_bit_pos save_bit_pos 0b{0}/{1} => {2}".format(bitstring, prefix_len, i+1)
    print(output)
