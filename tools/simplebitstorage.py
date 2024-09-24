import math
from typing import List, Optional, Callable

class SimpleBitStorage:
    MAGIC = [
        -1, -1, 0, -2147483648, 0, 0, 1431655765, 1431655765, 0, -2147483648, 0, 1, 858993459, 858993459, 0, 715827882, 715827882, 0, 613566756, 613566756, 0, -2147483648, 0, 2, 477218588, 477218588, 0, 429496729, 429496729, 0, 390451572, 390451572, 0, 357913941, 357913941, 0, 330382099, 330382099, 0, 306783378, 306783378, 0, 286331153, 286331153, 0, -2147483648, 0, 3, 252645135, 252645135, 0, 238609294, 238609294, 0, 226050910, 226050910, 0, 214748364, 214748364, 0, 204522252, 204522252, 0, 195225786, 195225786, 0, 186737708, 186737708, 0, 178956970, 178956970, 0, 171798691, 171798691, 0, 165191049, 165191049, 0, 159072862, 159072862, 0, 153391689, 153391689, 0, 148102320, 148102320, 0, 143165576, 143165576, 0, 138547332, 138547332, 0, -2147483648, 0, 4, 130150524, 130150524, 0, 126322567, 126322567, 0, 122713351, 122713351, 0, 119304647, 119304647, 0, 116080197, 116080197, 0, 113025455, 113025455, 0, 110127366, 110127366, 0, 107374182, 107374182, 0, 104755299, 104755299, 0, 102261126, 102261126, 0, 99882960, 99882960, 0, 97612893, 97612893, 0, 95443717, 95443717, 0, 93368854, 93368854, 0, 91382282, 91382282, 0, 89478485, 89478485, 0, 87652393, 87652393, 0, 85899345, 85899345, 0, 84215045, 84215045, 0, 82595524, 82595524, 0, 81037118, 81037118, 0, 79536431, 79536431, 0, 78090314, 78090314, 0, 76695844, 76695844, 0, 75350303, 75350303, 0, 74051160, 74051160, 0, 72796055, 72796055, 0, 71582788, 71582788, 0, 70409299, 70409299, 0, 69273666, 69273666, 0, 68174084, 68174084, 0, -2147483648, 0, 5
    ]

    def __init__(self, element_bits: int, size: int, data: Optional[List[int]] = None):
        if not (1 <= element_bits <= 32):
            raise ValueError("element_bits must be between 1 and 32")
        
        self.size = size
        self.bits = element_bits
        self.mask = (1 << element_bits) - 1
        self.values_per_long = 64 // element_bits
        i = 3 * (self.values_per_long - 1)
        self.divide_mul = self.MAGIC[i + 0]
        self.divide_mul_unsigned = self.divide_mul & 0xFFFFFFFF
        self.divide_add = self.MAGIC[i + 1]
        self.divide_add_unsigned = self.divide_add & 0xFFFFFFFF
        self.divide_shift = self.MAGIC[i + 2]
        j = (size + self.values_per_long - 1) // self.values_per_long

        if data is not None:
            if len(data) != j:
                raise ValueError(f"Invalid length given for storage, got: {len(data)} but expected: {j}")
            self.data = data
        else:
            self.data = [0] * j

    def cell_index(self, index: int) -> int:
        return (index * self.divide_mul_unsigned + self.divide_add_unsigned) >> 32 >> self.divide_shift

    def get_and_set(self, index: int, value: int) -> int:
        i = self.cell_index(index)
        l = self.data[i]
        j = (index - i * self.values_per_long) * self.bits
        k = (l >> j) & self.mask
        self.data[i] = (l & ~(self.mask << j)) | ((value & self.mask) << j)
        return k

    def set(self, index: int, value: int):
        i = self.cell_index(index)
        l = self.data[i]
        j = (index - i * self.values_per_long) * self.bits
        self.data[i] = (l & ~(self.mask << j)) | ((value & self.mask) << j)

    def get(self, index: int) -> int:
        i = self.cell_index(index)
        l = self.data[i]
        j = (index - i * self.values_per_long) * self.bits
        return (l >> j) & self.mask

    def get_raw(self) -> List[int]:
        return self.data

    def get_size(self) -> int:
        return self.size

    def get_bits(self) -> int:
        return self.bits

    def get_all(self, action: Callable[[int], None]):
        i = 0
        for l in self.data:
            for j in range(self.values_per_long):
                action(l & self.mask)
                l >>= self.bits
                i += 1
                if i >= self.size:
                    return

    def unpack(self, out: List[int]):
        i = len(self.data)
        j = 0
        for k in range(i - 1):
            l = self.data[k]
            for m in range(self.values_per_long):
                out[j + m] = l & self.mask
                l >>= self.bits
            j += self.values_per_long
        n = self.size - j
        if n > 0:
            o = self.data[i - 1]
            for p in range(n):
                out[j + p] = o & self.mask
                o >>= self.bits
