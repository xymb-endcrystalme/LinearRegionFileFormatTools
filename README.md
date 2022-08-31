# Linear region file format for Minecraft

Linear region format saves about 50% of disk space in OW and Nether and 95% in The End.
This repository hosts tools to convert between `.mca` and `.linear`.

## Supported software:

[LinearPaper](https://github.com/xymb-endcrystalme/LinearPaper) - Linear-enabled version of Paper. No further changes, 100% compatible with Paper. Precompiled binaries included.


[LinearPurpur](https://github.com/xymb-endcrystalme/LinearPurpur) - Linear-enabled version of Purpur. No further changes, 100% compatible with Purpur. Precompiled binaries included.


[LinearMultiPaper](https://github.com/xymb-endcrystalme/LinearMultiPaper) - MultiPaper with a few custom patches, including Linear region file format. No binaries available.

## Python prerequisites:

```apt install python3-pip
pip3 install pyzstd xxhash
```

## Usage:

```./mca_to_linear.py r.0.0.mca```

Will create r.0.0.linear in the same directory



```./linear_to_mca.py r.0.0.linear```

Will create r.0.0.mca in the same directory



```./linear_to_mca_directory.py threads compression_level source_dir destination_dir```


Suggested compression level is 6. Suggested threads is the amount of cores of the CPU.

This command converts all ```.mca``` files from source_dir to ```.linear``` in the destination_dir.

It checks file modification date, so you can convert 99% of your world at your leasure, and then finish the last 1% when the server is offline, thus achieving 5min downtime.

## Results:

An undisclosed world (overworld) converted on 5950x compressed from 227357M to 119912M at compression_level=6.

Compression took 22min 17s on 5950x.
