# MilkyWay — The Galactic CTF Orchestrator
# Usage: docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway

FROM golang:1.21-alpine AS go-builder
RUN go install github.com/ffuf/ffuf/v2@latest && \
    go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget git vim binwalk steghide exiftool tshark foremost \
    strace ltrace radare2 sqlmap hashcat john xxd binutils file \
    openssl build-essential nmap netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=go-builder /root/go/bin/ffuf /usr/local/bin/ffuf
COPY --from=go-builder /root/go/bin/nuclei /usr/local/bin/nuclei

RUN pip install --no-cache-dir pwntools ROPgadget ropper

WORKDIR /opt/milkyway
COPY . .
RUN pip install --no-cache-dir -e ".[llm]"

WORKDIR /workspace
VOLUME ["/workspace"]

RUN echo 'export PS1="🌌 milkyway:\w$ "' >> /root/.bashrc && \
    echo 'alias mw="milkyway"' >> /root/.bashrc

ENTRYPOINT ["/bin/bash"]
