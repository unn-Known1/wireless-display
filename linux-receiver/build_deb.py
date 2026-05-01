#!/usr/bin/env python3
"""
Build Debian package for Wireless Display Receiver
Creates a .deb package for Linux Mint/Debian-based distributions
"""

import os
import sys
import shutil
import subprocess
import tarfile
from pathlib import Path

PACKAGE_NAME = "wireless-display-receiver"
VERSION = "1.0.0"
ARCHITECTURE = "amd64"
MAINTAINER = "Wireless Display Team"
SECTION = "network"
DEPENDS = "python3 (>= 3.8), python3-pyqt6"
DESCRIPTION = """Use Android TV as secondary display over WiFi
 Virtual display receiver that streams desktop to Android TV via VNC protocol.
 Works with Wireless Display TV app on Android TV."""

def create_directories(tmp_dir):
    """Create debian package structure"""
    # Main package directories
    deb_dir = os.path.join(tmp_dir, f"{PACKAGE_NAME}_{VERSION}_{ARCHITECTURE}")
    data_dir = os.path.join(deb_dir, "data")
    debian_dir = os.path.join(deb_dir, "debian")

    os.makedirs(os.path.join(data_dir, "opt/wireless-display/receiver"))
    os.makedirs(os.path.join(data_dir, "usr/share/applications"))
    os.makedirs(os.path.join(data_dir, "usr/share/doc/wireless-display-receiver"))
    os.makedirs(debian_dir)

    return deb_dir, data_dir, debian_dir

def copy_files(data_dir):
    """Copy application files"""
    # Copy main application
    src_dir = os.path.dirname(os.path.abspath(__file__))
    app_src = os.path.join(src_dir, "wireless-display-receiver.py")
    app_dst = os.path.join(data_dir, "opt/wireless-display/receiver/wireless-display-receiver.py")
    shutil.copy(app_src, app_dst)

    # Make executable
    os.chmod(app_dst, 0o755)

def create_debian_files(debian_dir):
    """Create Debian control files"""

    # control file
    control_content = f"""Package: {PACKAGE_NAME}
Priority: optional
Section: {SECTION}
Architecture: {ARCHITECTURE}
Depends: {DEPENDS}
Maintainer: {MAINTAINER}
Description: Use Android TV as secondary display over WiFi
 Virtual display receiver that streams desktop to Android TV via VNC protocol.
 Works with Wireless Display TV app on Android TV.
 .
 Features:
  - VNC server for remote display
  - Easy setup with system tray
  - Configurable resolution
  - Auto-discovery support
"""

    with open(os.path.join(debian_dir, "control"), "w") as f:
        f.write(control_content)

    # postinst script
    postinst = """#!/bin/bash
# Post-installation script
update-desktop-database ~/.local/share/applications 2>/dev/null || true
chmod +x /opt/wireless-display/receiver/wireless-display-receiver.py
exit 0
"""
    with open(os.path.join(debian_dir, "postinst"), "w") as f:
        f.write(postinst)
    os.chmod(os.path.join(debian_dir, "postinst"), 0o755)

    # prerm script
    prerm = """#!/bin/bash
# Pre-removal script
pkill -f wireless-display-receiver.py 2>/dev/null || true
exit 0
"""
    with open(os.path.join(debian_dir, "prerm"), "w") as f:
        f.write(prerm)
    os.chmod(os.path.join(debian_dir, "prerm"), 0o755)

    # copyright file
    copyright = """Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: wireless-display-receiver
Upstream-Contact: Wireless Display Team
License: MIT
Copyright: 2024 Wireless Display Team

Files:
 *
Copyright: 2024 Wireless Display Team
License: MIT

License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
"""
    with open(os.path.join(debian_dir, "copyright"), "w") as f:
        f.write(copyright)

    # changelog file
    changelog = f"{PACKAGE_NAME} ({VERSION}) stable; urgency=low\n"
    changelog += f"\n  * Initial release\n\n -- {MAINTAINER}  Thu, 01 May 2024 00:00:00 +0000\n"

    with open(os.path.join(debian_dir, "changelog"), "w") as f:
        f.write(changelog)

def create_desktop_entry(data_dir):
    """Create desktop entry file"""
    desktop_content = """[Desktop Entry]
Name=Wireless Display Receiver
Comment=Use Android TV as secondary display
Exec=/opt/wireless-display/receiver/wireless-display-receiver.py
Icon=wireless-display
Terminal=false
Type=Application
Categories=Network;RemoteAccess;
Keywords=display;vnc;remote;wireless;
StartupNotify=true
"""
    with open(os.path.join(data_dir, "usr/share/applications/wireless-display-receiver.desktop"), "w") as f:
        f.write(desktop_content)

def build_deb(tmp_dir, output_dir):
    """Build the .deb package"""
    pkg_dir = os.path.join(tmp_dir, f"{PACKAGE_NAME}_{VERSION}_{ARCHITECTURE}")

    # Create tar.gz for data
    data_dir = os.path.join(pkg_dir, "data")
    os.chdir(data_dir)
    tar_data = tarfile.open(os.path.join(tmp_dir, f"data.tar.gz"), "w:gz")
    for root, dirs, files in os.walk("."):
        for file in files:
            tar_data.add(os.path.join(root, file))
    tar_data.close()

    # Create debian tar.gz
    debian_dir = os.path.join(pkg_dir, "debian")
    os.chdir(debian_dir)
    tar_deb = tarfile.open(os.path.join(tmp_dir, f"debian.tar.gz"), "w:gz")
    for root, dirs, files in os.walk("."):
        for file in files:
            tar_deb.add(os.path.join(root, file))
    tar_deb.close()

    # Create debian-binary
    with open(os.path.join(tmp_dir, "debian-binary"), "w") as f:
        f.write("2.0\n")

    # Combine into .deb
    deb_file = os.path.join(output_dir, f"{PACKAGE_NAME}_{VERSION}_{ARCHITECTURE}.deb")
    os.chdir(tmp_dir)

    with open(deb_file, "wb") as out:
        # ar archive
        # Simple ar creation (for basic compatibility)
        import struct

        # ar header for debian-binary
        out.write(b"!<arch>\n")
        out.write(b"debian-binary       ")
        out.write(b"12560172136 ")
        out.write(b"0     ")
        out.write(b"0     ");
        out.write(b"0  `\n")
        with open(os.path.join(tmp_dir, "debian-binary"), "rb") as f:
            out.write(f.read())
        out.write(b"\n")

        # ar header for data.tar.gz
        out.write(b"data.tar.gz        ")
        out.write(f"{os.path.getsize(os.path.join(tmp_dir, 'data.tar.gz')): <10}".encode())
        out.write(b"12560172136 ")
        out.write(b"0     ")
        out.write(b"0     ");
        out.write(b"0  `\n")
        with open(os.path.join(tmp_dir, "data.tar.gz"), "rb") as f:
            out.write(f.read())
        out.write(b"\n")

        # ar header for debian.tar.gz
        out.write(b"debian.tar.gz      ")
        out.write(f"{os.path.getsize(os.path.join(tmp_dir, 'debian.tar.gz')): <10}".encode())
        out.write(b"12560172136 ");
        out.write(b"0     ");
        out.write(b"0     ");
        out.write(b"0  `\n")
        with open(os.path.join(tmp_dir, "debian.tar.gz"), "rb") as f:
            out.write(f.read())
        out.write(b"\n")

    return deb_file

def main():
    # Setup directories
    src_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(src_dir, "deb_build")
    output_dir = src_dir

    # Clean and create temp directory
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    print("Building Debian package...")

    # Create package structure
    deb_dir, data_dir, debian_dir = create_directories(tmp_dir)
    print("Created package structure")

    # Copy files
    copy_files(data_dir)
    print("Copied application files")

    # Create Debian control files
    create_debian_files(debian_dir)
    print("Created Debian control files")

    # Create desktop entry
    create_desktop_entry(data_dir)
    print("Created desktop entry")

    # Build .deb package
    deb_file = build_deb(tmp_dir, output_dir)
    print(f"\nPackage built successfully: {deb_file}")

    # Cleanup
    shutil.rmtree(tmp_dir)

    return deb_file

if __name__ == "__main__":
    main()