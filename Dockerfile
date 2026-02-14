FROM ubuntu:latest
LABEL authors="ahmetcolak"

ENTRYPOINT ["top", "-b"]