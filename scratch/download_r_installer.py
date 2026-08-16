import urllib.request
import re

url = "https://cran.r-project.org/bin/windows/base/"
print("Fetching CRAN download page...")
html = urllib.request.urlopen(url).read().decode('utf-8')
match = re.search(r'href="(R-[\d\.]+-win\.exe)"', html)
if match:
    download_url = "https://cran.r-project.org/bin/windows/base/" + match.group(1)
    target_path = r"C:\WEB CASE STUDY\R_installer.exe"
    print(f"Downloading Native Windows R Installer from: {download_url}")
    urllib.request.urlretrieve(download_url, target_path)
    print(f"✅ Download Complete: {target_path}")
else:
    print("Could not find installer download URL")
