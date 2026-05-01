#!/usr/bin/env python3
"""
Build Debian package for Wireless Display Receiver
Uses shell tar and ar commands
"""

import os
import shutil
import subprocess

PACKAGE_NAME = "wireless-display-receiver"
VERSION = "1.0.0"
ARCHITECTURE = "amd64"
MAINTAINER = "Wireless Display Team"
SECTION = "network"
DEPENDS = "python3 (>= 3.8), python3-pyqt6"

def main():
    src_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.join(src_dir, "deb_build")
    output_dir = src_dir

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    print("Building Debian package...")

    # Create structure
    data_dir = os.path.join(tmp_dir, "data")
    debian_dir = os.path.join(tmp_dir, "debian")
    os.makedirs(os.path.join(data_dir, "opt/wireless-display/receiver"))
    os.makedirs(os.path.join(data_dir, "usr/share/applications"))
    os.makedirs(debian_dir)

    # Copy files
    app_src = os.path.join(src_dir, "wireless-display-receiver.py")
    app_dst = os.path.join(data_dir, "opt/wireless-display/receiver/wireless-display-receiver.py")
    shutil.copy(app_src, app_dst)
    os.chmod(app_dst, 0o755)

    # Desktop entry
    desktop = """[Desktop Entry]
Name=Wireless Display Receiver
Comment=Use Android TV as secondary display
Exec=python3 /opt/wireless-display/receiver/wireless-display-receiver.py
Terminal=false
Type=Application
Categories=Network;RemoteAccess;
"""
    with open(os.path.join(data_dir, "usr/share/applications/wireless-display-receiver.desktop"), "w") as f:
        f.write(desktop)

    # Control file
    control = f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: {SECTION}
Priority: optional
Architecture: {ARCHITECTURE}
Depends: {DEPENDS}
Maintainer: {MAINTAINER}
Description: Use Android TV as secondary display over WiFi
 Virtual display receiver that streams desktop to Android TV via VNC protocol.
 Works with Wireless Display TV app on Android TV.
"""
    with open(os.path.join(debian_dir, "control"), "w") as f:
        f.write(control)

    # Postinst
    postinst = """#!/bin/bash
chmod +x /opt/wireless-display/receiver/wireless-display-receiver.py
exit 0
"""
    with open(os.path.join(debian_dir, "postinst"), "w") as f:
        f.write(postinst)
    os.chmod(os.path.join(debian_dir, "postinst"), 0o755)

    # Prerm
    prerm = """#!/bin/bash
pkill -f wireless-display-receiver.py 2>/dev/null || true
exit 0
"""
    with open(os.path.join(debian_dir, "prerm"), "w") as f:
        f.write(prerm)
    os.chmod(os.path.join(debian_dir, "prerm"), 0o755)

    print("Created package structure")

    # Create tar.gz files
    subprocess.run(["tar", "-czf", "data.tar.gz", "-C", data_dir, "."],
                   cwd=tmp_dir, check=True)
    print("Created data.tar.gz")

    subprocess.run(["tar", "-czf", "control.tar.gz", "-C", debian_dir, "."],
                   cwd=tmp_dir, check=True)
    print("Created control.tar.gz")

    # Create debian-binary
    with open(os.path.join(tmp_dir, "debian-binary"), "w") as f:
        f.write("2.0\n")

    # Build .deb with ar
    deb_file = os.path.join(output_dir, f"{PACKAGE_NAME}_{VERSION}_{ARCHITECTURE}.deb")
    subprocess.run(["ar", "rcs", deb_file,
                   os.path.join(tmp_dir, "debian-binary"),
                   os.path.join(tmp_dir, "control.tar.gz"),
                   os.path.join(tmp_dir, "data.tar.gz")],
                  check=True)

    print(f"\nPackage built: {deb_file}")

    # Verify
    result = subprocess.run(["file", deb_file], capture_output=True, text=True)
    print(f"Package type: {result.stdout.strip()}")

    result = subprocess.run(["dpkg-deb", "--info", deb_file], capture_output=True, text=True)
    if result.returncode == 0:
        print("Package info:\n" + result.stdout)
    else:
        print("dpkg-deb info:", result.stderr[:200])

    shutil.rmtree(tmp_dir)
    return deb_file

if __name__ == "__main__":
    main()