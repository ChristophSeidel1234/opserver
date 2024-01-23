FROM python

WORKDIR /usr/src/app

RUN pip install --no-cache-dir packaging requests codetiming boto3 flask pyyaml secure prometheus_client

COPY src .
COPY ../config.yaml config/config.yaml
EXPOSE 8080

#ENTRYPOINT ["python3", "/usr/src/app/main.py"]
CMD ["sleep", "infinity"]
