FROM ubuntu:latest
RUN apt-get update -y --fix-missing
RUN apt-get install -y python3 python3-dev python3-pip build-essential git
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
EXPOSE 5000
CMD ["app.py"]