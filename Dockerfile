FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/opt/app \
    PORT=8080

WORKDIR ${APP_HOME}

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY resources ./resources
COPY static ./static
COPY scripts/start.sh /usr/local/bin/start.sh

RUN chmod +x /usr/local/bin/start.sh \
    && chgrp -R 0 ${APP_HOME} /usr/local/bin/start.sh \
    && chmod -R g=u ${APP_HOME} /usr/local/bin/start.sh

USER 1001

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/start.sh"]
