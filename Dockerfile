# ─────────────────────────────────────────────────────────────────────────────
#  MilkyWay CTF Suite — Production Docker Image
#  `docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway`
#  Everything pre-installed. Zero "tool not found" errors.
# ─────────────────────────────────────────────────────────────────────────────

FROM kalilinux/kali-rolling:latest AS base

LABEL maintainer="Kazim <kazim@milkyway-ctf.dev>"
LABEL description="MilkyWay — The Galactic CTF Orchestrator v2.0"
LABEL version="2.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MILKYWAY_DOCKER=1
ENV TERM=xterm-256color
ENV HOME=/root

# ── System packages ────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core
    python3 python3-pip python3-dev python3-venv \
    git curl wget \
    # Build tools
    build-essential libffi-dev libssl-dev \
    # Forensics
    binutils file xxd exiftool foremost \
    binwalk steghide tshark wireshark-common \
    # Web
    sqlmap nikto \
    # Reverse Engineering
    radare2 ltrace strace gdb \
    # Binary exploitation
    checksec \
    # Password / crypto
    hashcat john john-data wordlists \
    # Network
    nmap whois dnsutils netcat-openbsd \
    # Mobile
    apktool adb \
    # Misc
    golang-go p7zip-full unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Go tools ───────────────────────────────────────────────────────────────────
ENV GOPATH=/root/go
ENV PATH="$GOPATH/bin:/usr/local/go/bin:$PATH"
RUN go install github.com/ffuf/ffuf/v2@latest && \
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# ── Python security tools (all pip-installable) ────────────────────────────────
RUN pip3 install --no-cache-dir --break-system-packages \
    # MilkyWay core deps
    click>=8.1 rich>=13.7 textual>=0.47 \
    requests>=2.31 httpx>=0.27 \
    beautifulsoup4>=4.12 lxml>=4.9 \
    pycryptodome>=3.20 pyOpenSSL>=24.0 cryptography>=42.0 \
    sympy>=1.12 \
    pillow>=10.0 \
    capstone>=5.0 \
    pwntools>=4.12 \
    ROPgadget>=7.3 \
    androguard>=4.1 \
    dnspython>=2.6 \
    python-whois>=0.9 \
    PyJWT>=2.8 \
    passlib>=1.7 paramiko>=3.4 \
    openai>=1.30 \
    pyyaml>=6.0 python-dateutil>=2.8 humanize>=4.9 \
    colorama>=0.4 tqdm>=4.66 tabulate>=0.9 \
    # Extra security tools
    sqlmap \
    impacket \
    pyshark \
    construct>=2.10 \
    scapy>=2.5

# ── MilkyWay itself ────────────────────────────────────────────────────────────
WORKDIR /opt/milkyway
COPY . .
RUN pip3 install --no-cache-dir --break-system-packages -e .

# ── Wordlists ──────────────────────────────────────────────────────────────────
RUN mkdir -p /usr/share/wordlists && \
    cp /usr/share/wordlists/rockyou.txt.gz /usr/share/wordlists/ 2>/dev/null && \
    gunzip -f /usr/share/wordlists/rockyou.txt.gz 2>/dev/null && \
    wget -q "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt" \
         -O /usr/share/wordlists/common.txt 2>/dev/null || \
    cp /opt/milkyway/milkyway/data/wordlists/common.txt /usr/share/wordlists/common.txt

# ── Shell setup ────────────────────────────────────────────────────────────────
RUN echo 'alias mw=milkyway' >> /root/.bashrc && \
    echo 'export TERM=xterm-256color' >> /root/.bashrc && \
    _MILKYWAY_COMPLETE=bash_source milkyway > /root/.milkyway_complete.bash 2>/dev/null || true && \
    echo 'source /root/.milkyway_complete.bash 2>/dev/null' >> /root/.bashrc

WORKDIR /workspace
VOLUME ["/workspace"]

ENTRYPOINT ["milkyway"]
CMD []
