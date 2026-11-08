# Tools for labels.py: zint for code generation, zxing-cpp for verification,
# pyusb and libusb for direct USB access to the printer.
{
  pkgs ? import <nixpkgs> { },
}:
pkgs.mkShell {
  packages = [
    pkgs.zint-qt
    (pkgs.python3.withPackages (p: [
      p.pillow
      p.pyusb
      p.zxing-cpp
    ]))
  ];
  DYLD_FALLBACK_LIBRARY_PATH = "${pkgs.libusb1}/lib";
}
