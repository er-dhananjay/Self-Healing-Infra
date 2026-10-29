FROM python:3.12-slim
# Docker CLI (static binary) so Ansible can restart containers through the mounted socket
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker
RUN pip install --no-cache-dir ansible-core==2.17.7
ENV ANSIBLE_HOST_KEY_CHECKING=False \
    ANSIBLE_DEPRECATION_WARNINGS=False \
    ANSIBLE_NOCOLOR=1 \
    PYTHONUNBUFFERED=1
COPY ansible /ansible
COPY healer/webhook.py /app/webhook.py
EXPOSE 5001
CMD ["python", "/app/webhook.py"]
