FROM ubuntu:22.04 AS builder

FROM ghcr.io/gzctf/challenge-base/socat:alpine

COPY src/start.sh /start.sh

RUN cp -R /lib* /home/ctf && \
    mkdir -p /home/ctf/dev && \
    (mknod /home/ctf/dev/null c 1 3 || true) && \
    (mknod /home/ctf/dev/zero c 1 5 || true) && \
    (mknod /home/ctf/dev/random c 1 8 || true) && \
    (mknod /home/ctf/dev/urandom c 1 9 || true) && \
    (chmod 666 /home/ctf/dev/* 2>/dev/null || true) && \
    mkdir -p /home/ctf/bin && \
    (cp /bin/sh /home/ctf/bin || true) && \
    (cp /bin/ls /home/ctf/bin || true) && \
    (cp /bin/cat /home/ctf/bin || true) && \
    (cp /bin/base64 /home/ctf/bin || true) && \
    chmod +x /start.sh

WORKDIR /home/ctf

COPY --from=builder /lib64/ld-linux-x86-64.so.2 /home/ctf/lib64/
COPY --from=builder /lib/x86_64-linux-gnu/libc.so.6 /home/ctf/lib/x86_64-linux-gnu/

COPY --chown=ctf:ctf src/pwn ./vuln
RUN chmod 500 ./vuln

CMD ["/start.sh"]