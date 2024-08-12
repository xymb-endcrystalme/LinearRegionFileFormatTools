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

    def tearDown(self):
        shutil.rmtree(self.test_dir)

#    def test_load_mca(self):
#        mca_file_path = "/home/xymb/paperdocker/r.0.0.mca"
#        region = mclinear.open_region_linear("/home/xymb/spawn/region/r.-10.3.linear")
#        region = mclinear.open_region_anvil("/home/xymb/paperdocker/dockervolume/world/entities/r.0.0.mca")

#        mca_file_path = os.path.join(script_dir, "1.12.2", "r.0.0.mca")
#        region = mclinear.open_region_anvil(mca_file_path)
#        linear_file_path = os.path.join(self.test_dir, "r.0.0.linear")

#        print(f"Size of {linear_file_path}: {os.path.getsize(linear_file_path)} bytes")
    def _test_aaa(self):
        file = "/home/xymb/spawn/region/r.0.0.linear"
        region = mclinear.open_region_linear("/home/xymb/stash/r.0.0.linear")
        #region = mclinear.open_region_linear_v2("/home/xymb/minecraft/Abomination_1.21/run/world/region/r.0.0.linear")
        mclinear.write_region_linear_v2("/home/xymb/r.0.0.linearv2", region)

    def _test_big_private(self):
        DIRS = ["/home/xymb/spawn/poi/", "/home/xymb/spawn/entities/", "/home/xymb/spawn/region/"]
        for dir in DIRS:
            for file in os.listdir(dir):
                file = os.path.join(dir, file)
                if file.endswith(".linear"):
                    print("Testing " + file)
                    region = mclinear.open_region_linear(file)
                elif file.endswith(".mca"):
                    print("Testing " + file)
                    region = mclinear.open_region_anvil(file)
                else:
                    print("Skipping " + file)
                    continue

                region.nbt_features = {"shulker_deduplication": 1, "light_removal": 2}
                grid_size = random.choice([1, 2, 4, 8, 16, 32])
                compression_level = random.choice([-1, 0, 1, 2, 3, 4, 5, 6])

                test_file = os.path.join(self.test_dir, "filename.linear") # Linearv2 keeps coordinates in the header, filename doesn't matter
                mclinear.write_region_linear_v2(test_file, region, compression_level=compression_level, grid_size=grid_size)
                region2 = mclinear.open_region_linear_v2(test_file)

                self.assertDictEqual(region.nbt_features, region2.nbt_features)
                self.compare_regions(region, region2)

                test_file = os.path.join(self.test_dir, "r.%d.%d.linear" % (region.region_x, region.region_z))
                mclinear.write_region_linear(test_file, region, compression_level=compression_level)
                region2 = mclinear.open_region_linear(test_file)

                self.assertDictEqual({}, region2.nbt_features)
                self.compare_regions(region, region2)

                test_file = os.path.join(self.test_dir, "r.%d.%d.mca" % (region.region_x, region.region_z))
                mclinear.write_region_anvil(test_file, region)
                region2 = mclinear.open_region_anvil(test_file)

                self.assertDictEqual({}, region2.nbt_features)
                self.compare_regions(region, region2)

    def test_write_dict_to_bytes_and_read_dict_from_bytes(self):
        original_dict = {
            "shulker_deduplication": 1,
            "light_removal": 2,
            "example_key": 123456
        }
        serialized_bytes = mclinear.write_dict_to_bytes(original_dict)
        deserialized_dict, length = mclinear.read_dict_from_bytes(serialized_bytes)
        self.assertEqual(length, len(serialized_bytes))
        self.assertEqual(original_dict, deserialized_dict)

    def compare_regions(self, region, region2):
        self.assertEqual(region.region_x, region2.region_x)
        self.assertEqual(region.region_z, region2.region_z)
        self.assertEqual(region.mtime, region2.mtime)

        self.assertEqual(len(region.timestamps), len(region2.timestamps))
        for i in range(len(region.timestamps)):
            self.assertEqual(region.timestamps[i], region2.timestamps[i])
#        self.assertListEqual(region.timestamps, region2.timestamps)

        self.assertEqual(len(region.chunks), len(region2.chunks))

        for chunk1, chunk2 in zip(region.chunks, region2.chunks):
            if chunk1 is None and chunk2 is None:
                continue
            self.assertEqual(chunk1 is None, chunk2 is None)
            self.assertEqual(chunk1.x, chunk2.x)
            self.assertEqual(chunk1.z, chunk2.z)
            self.assertEqual(chunk1.raw_chunk, chunk2.raw_chunk)



if __name__ == '__main__':
    unittest.main()
