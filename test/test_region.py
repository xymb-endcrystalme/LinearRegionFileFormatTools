import unittest
import mclinear
import tempfile
import os
import shutil
import hashlib
import random

script_dir = os.path.dirname(os.path.abspath(__file__))

class TestExample(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.subdir_1_12_2 = os.path.join(self.test_dir, "1.12.2")
        os.makedirs(self.subdir_1_12_2, exist_ok=True)

        # Copy the required files
#        shutil.copy(os.path.join(script_dir, "1.12.2", "r.0.0.mca"), self.subdir_1_12_2)
#        shutil.copy(os.path.join(script_dir, "1.12.2", "r.0.0_oversized_0_1.nbt"), self.subdir_1_12_2)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_save(self):
        VALID_NBT_FEATURES = {"feature_1": 1, "feature_2": 2}

        def verify_region(region):
            sha256_hash = hashlib.sha256()
            sha256_hash_nbt = hashlib.sha256()
            for i, chunk in enumerate(region.chunks):
                if chunk is not None:
                    if i == 0:
                        nbt = str(chunk.as_nbtlib()).encode()
                        sha256_hash_nbt.update(nbt)
                        self.assertTrue(b"Xymb" in chunk.raw_chunk)
                        self.assertTrue(b"Xymb" in nbt)
                    if i == 1:
                        self.assertFalse(b"Xymb" in chunk.raw_chunk)
                    sha256_hash.update(chunk.raw_chunk)

            self.assertEqual(sha256_hash.hexdigest(), "b02232ccb3443d287c91e21f0ea51652899ea88d6df844a041c71d1674aebc7a")
            self.assertEqual(sha256_hash_nbt.hexdigest(), "8c45ed4528ebf45d9083dc7ebca65cfca8e16bec65774a310074df238fb6dc40")

        region = mclinear.open_region_anvil(os.path.join(script_dir, "1.12.2", "r.0.0.mca"))
        verify_region(region)
        region = mclinear.open_region_linear(os.path.join(script_dir, "1.12.2", "r.0.0.linear"))
        verify_region(region)
        region = mclinear.open_region_linear_v2(os.path.join(script_dir, "1.12.2", "r.0.0.linearv2"))
        verify_region(region)
        self.assertDictEqual(region.nbt_features, VALID_NBT_FEATURES)

        mclinear.write_region_anvil(os.path.join(self.test_dir, "r.0.0.mca"), region, compression_level=1)
        region2 = mclinear.open_region_anvil(os.path.join(self.test_dir, "r.0.0.mca"))
        verify_region(region2)
        self.assertDictEqual(region2.nbt_features, {})
        mclinear.write_region_linear(os.path.join(self.test_dir, "r.0.0.linear"), region, compression_level=1)
        region2 = mclinear.open_region_linear(os.path.join(self.test_dir, "r.0.0.linear"))
        verify_region(region2)
        self.assertDictEqual(region2.nbt_features, {})
        mclinear.write_region_linear_v2(os.path.join(self.test_dir, "r.0.0.linear"), region, compression_level=1)
        region2 = mclinear.open_region_linear_v2(os.path.join(self.test_dir, "r.0.0.linear"))
        self.assertDictEqual(region2.nbt_features, VALID_NBT_FEATURES)
        verify_region(region2)



        # print(f"SHA256 hash of all raw chunk data: {sha256_hash.hexdigest()}")
        # print(f"SHA256 hash of NBT: {sha256_hash_nbt.hexdigest()}")

        region.nbt_features = {"feature_1": 1, "feature_2": 2}
#        mclinear.write_region_linear(os.path.join(script_dir, "1.12.2", "r.0.0.linear"), region, compression_level=19)
#        mclinear.write_region_linear_v2(os.path.join(script_dir, "1.12.2", "r.0.0.linearv2"), region, compression_level=19)
#        mclinear.write_region_linear(os.path.join(script_dir, "1.12.2", "r.0.0.linear"), region, compression_level=1)
#        mclinear.write_region_linear_v2(os.path.join(script_dir, "1.12.2", "r.0.0.linearv2"), region, compression_level=1)

#        region2 = mclinear.open_region_linear("/home/xymb/minecraft/Abomination_1.21/unittestBlobs/r.0.0.linear")

    def test_existence_bitmap_serialization(self):
        random_bitmap = [random.choice([True, False]) for _ in range(1024)]
        serialized = mclinear.serialize_existence_bitmap(random_bitmap)
        self.assertEqual(len(serialized), 128, "Serialized bitmap should be 128 bytes long")
        deserialized = mclinear.deserialize_existence_bitmap(serialized)
        self.assertEqual(random_bitmap, deserialized, "Deserialized bitmap should match the original")

if __name__ == '__main__':
    unittest.main()
