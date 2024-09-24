import math
from typing import List, Optional, Callable

class SecondBitStorage:
    def __init__(self, element_bits: int, size: int, data: Optional[List[int]] = None):
        if not (1 <= element_bits <= 32):
            raise ValueError("element_bits must be between 1 and 32")
        
        self.size = size
        self.bits = element_bits
        self.mask = (1 << element_bits) - 1
        self.values_per_long = 64 // element_bits
        j = (size + self.values_per_long - 1) // self.values_per_long

        if data is not None:
            if len(data) != j:
                raise ValueError(f"Invalid length given for storage, got: {len(data)} but expected: {j}")
            self.data = data
        else:
            self.data = [0] * j

    def cell_index(self, index: int) -> int:
        return index // self.values_per_long

    def get_and_set(self, index: int, value: int) -> int:
        i = self.cell_index(index)
        l = self.data[i]
        j = (index % self.values_per_long) * self.bits
        k = (l >> j) & self.mask
        self.data[i] = (l & ~(self.mask << j)) | ((value & self.mask) << j)
        return k

    def set(self, index: int, value: int):
        i = self.cell_index(index)
        l = self.data[i]
        j = (index % self.values_per_long) * self.bits
        self.data[i] = (l & ~(self.mask << j)) | ((value & self.mask) << j)

    def get(self, index: int) -> int:
        i = self.cell_index(index)
        l = self.data[i]
        j = (index % self.values_per_long) * self.bits
        return (l >> j) & self.mask

    def get_raw(self) -> List[int]:
        ret = list()
        for num in self.data:
            if num > 1 << 63:
                num = - 1 << 63 - num
        return self.data[ret]

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
