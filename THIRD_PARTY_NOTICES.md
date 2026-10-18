# Third-party notices

BatteryTray references the Beiying battery request/response implementation in
JKWTCN/BatteryMonitor (MIT, Copyright (c) 2026 JKWTCN).
Source: https://github.com/JKWTCN/BatteryMonitor
The upstream MIT text is retained in licenses/BatteryMonitor-MIT.txt.

Compx protocol fields were checked against ATK HUB's served web controller and
public protocol descriptions. ATK's proprietary JavaScript is not bundled here.
The project does not redistribute vendor firmware or vendor drivers.

Runtime dependencies:
- hidapi Python binding: https://github.com/trezor/cython-hidapi (see bundled license texts)
- HIDAPI library: https://github.com/libusb/hidapi (see bundled license texts)
- Pillow: https://python-pillow.github.io/ (HPND and bundled notices)
- pystray: https://github.com/moses-palmer/pystray (LGPLv3)
- six: https://github.com/benjaminp/six (MIT)
- Python: https://www.python.org/ (PSF license)
- Tcl/Tk: https://www.tcl-lang.org/ (see bundled Tcl/Tk license texts)

The binary is distributed as a directory bundle, with dynamically loadable
Python modules and native libraries, not a sealed single-file executable.
Source and build instructions accompany the download. Users may modify or
replace LGPL pystray components; this project imposes no restriction on reverse
engineering for debugging those modifications. Matching pystray Python source
is included under licenses/source/ for convenience.

Build tool: PyInstaller, GPL with bootloader distribution exception. Its license
and exception are bundled when available. Package metadata license files are
collected verbatim under licenses/; retaining a file does not imply every
optional dependency named in it is used.
